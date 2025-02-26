import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import re
import os
import logging_helper
from collections import deque
import threading
import traceback


#Some config data 
BASE_WEBSITE = 'https://www.nutritionvalue.org'
FOODS_START_MOD = '/foods_start_with_'
BRANDS_START_MOD = 'food_brand_starts_with_'
SITE_END = '.html'
PAGE_COUNTER = 'page_'
LETTER_LIST = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'Y', 'X', 'Z']

ITEMS_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/items.csv'
UNITLU_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/unit_lu.csv'
CONVJUNC_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/conversion_junc.csv'
NUTLU_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/nutrient_lu.csv'
NUTCAT_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/nutrient_category_lu.csv'
NUTJUNC_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/nutrient_junk.csv'
RESTART_PATH = '/home/bg-labs/bg_labs/fms/database/nutrition/data/restart.txt'



#shared event to manage stopping the script
stop_event = threading.Event()

def stop_listener():
    """
    Behavior:
    - Waits for the user to press the Enter key.
    - Prints a message indicating the script is stopping and requests patience during the cleanup process.
    - Sets a shared `stop_event` flag, signaling the main script to stop.
    """
    input("Press Enter to Stop the script...\n")
    print("Stopping the Nutrition Gather...Please be patient while we clean up you will be notified when it is safe to close")
    stop_event.set()

def get_page_source(driver: webdriver, url: str)->BeautifulSoup:
    """
    Retrieves the page source of a given URL using a Selenium WebDriver and parses it into a BeautifulSoup object.

    Parameters:
        driver (webdriver): An instance of Selenium's WebDriver used to interact with the web browser.
        url (str): The URL of the webpage to retrieve.

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the parsed HTML content of the webpage.

    Raises:
        Exception: If the URL cannot be reached, an error message is logged, and the function returns None.

    Side Effects:
        - Logs an error message if the URL cannot be accessed using the `logging_helper.add_to_log` function.
        - Prints an error message to the console.
    """
    
    try:
        driver.get(url)
        bs = BeautifulSoup(driver.page_source, 'html.parser')
        return bs
    except:
        error = "Can't Reach URL"
        print(error + ':', url)
        logging_helper.add_to_log(error, url, False)
        
def get_table_links(bs: BeautifulSoup)->list:
    """
    Extracts all links (<a> elements) with the class 'table_item_name' from a second-level table.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object containing the parsed HTML content.

    Returns:
        list: A list of <a> elements with the class 'table_item_name'.

    Raises:
        ValueError: If no matching elements are found in the table.
    """

    items = bs.find_all('a', {'class': 'table_item_name'})

    if not items:
        raise ValueError("Can't get items from 2nd level table")
    
    return items

def get_item_name(bs: BeautifulSoup)->str:
    """
    Extracts the item name from an item page.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object representing the parsed HTML content of the item page.

    Returns:
        str: The name of the item as a string.

    Raises:
        ValueError: If the item name cannot be located in the HTML content.
    """

    name = bs.find('h1', {'id': 'food-name'}).get_text()

    if not name:
        raise ValueError("Can't Locate Name of Item", False)
    
    return name

def split_brand(name: str)->tuple[str, str]:
    """
    Splits a name string into brand and item components if the name includes the word 'by'.

    Parameters:
        name (str): A string representing the name to be checked and split.

    Returns:
        tuple[str, str]: 
            - A tuple `(brand, item)` if the name contains the word 'by', where:
                - `brand` is the part before 'by'.
                - `item` is the part after 'by'.
            - A tuple `(name, None)` if the name does not contain the word 'by'.
    """

    rtnValue = name.split(' by ') 

    return rtnValue[0], rtnValue[1]

def gather_item_info(bs: BeautifulSoup, items: pd.DataFrame, unit_lu: pd.DataFrame)->tuple[int, pd.DataFrame, pd.DataFrame]:
    """
    Gathers and processes information about an item from a BeautifulSoup object, updates the provided dataframes, 
    and returns the updated data and item ID.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object containing the parsed HTML of the item's page.
        items (pd.DataFrame): A Pandas DataFrame containing the current dataset of items.
        unit_lu (pd.DataFrame): A Pandas DataFrame serving as a lookup table for units.

    Returns:
        tuple[int, pd.DataFrame, pd.DataFrame]: 
            - `cur_item_id` (int): The unique ID of the newly added item.
            - `items` (pd.DataFrame): The updated items DataFrame with the new item added.
            - `unit_lu` (pd.DataFrame): The updated unit lookup DataFrame with new units added, if applicable.

    Raises:
        ValueError: 
            - If the item name is already in dataset.
            - If the function fails to retrieve `cur_item_id`.

    Notes:
        -The Items DataFrame needs to contain columns corresponding to the keys in `new_row`
    """

    new_row = {'item_id': None, 'NLEA_unit': None, 'NLEA_val': None, 'ammount': None, 'ammount_unit': None, 'upc': None, 'ingredient_list': None}
    name = get_item_name(bs)
    if ' by ' in name:
        new_row['name'], new_row['brand'] = split_brand(name)
    else:
        new_row['name'] = name
        new_row['brand'] = ''


    row_values = items[(items['name'] == new_row['name']) & (items['brand'] == new_row['brand'])]
    if not row_values.empty:
        raise ValueError("We have Duplicate Row, [" + new_row['name'] + new_row['brand']+"]", False)
    
    new_row['NLEA_val'],  unit, new_row['ammount'], amt_unit = get_NLEA_info(bs)

    new_row['NLEA_unit'], unit_lu = get_unit_id(unit, unit_lu)
    new_row['ammount_unit'], unit_lu = get_unit_id(amt_unit, unit_lu)

    new_row['ingredient_list'] = get_ingredient(bs)
    new_row['upc'] = get_UPC(bs)



    cur_item_id, items = get_item_id(new_row, items)

    if not cur_item_id:
        ValueError("Failed to get cur_item_id", False)

    return cur_item_id, items, unit_lu

def get_NLEA_info(bs: BeautifulSoup) -> tuple[str, float, float]:
    """
    Extracts the NLEA serving unit, unit value, and mass from an item's HTML page.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object representing the parsed HTML content of the item's page.

    Returns:
        tuple[str, float, float]: A tuple containing:
            - NLEA serving unit (str): The unit of the NLEA serving.
            - Unit value (float): The numeric value associated with the unit.
            - Mass (float): The mass or amount corresponding to the serving size.

    Raises:
        ValueError: If the required NLEA information cannot be located or parsed.

    Notes:
        - This function relies on the `split_unit_value_and_ammount` helper function to parse the extracted `value`.
        - Ensure that the HTML structure includes an `<option>` tag with the `selected="selected"` attribute and a `value` attribute.
    """
    NLEA_info = bs.find('option', selected="selected")
    if NLEA_info:
        NLEA_info = NLEA_info.get('value')
        return split_unit_value_and_ammount(NLEA_info)
    raise ValueError("NLEA information not found on the page.")

def split_unit_value_and_ammount(NLEA_info: str)->tuple[float, str, str, float, str]:
    """
    Parses a string containing NLEA information and extracts the value, unit, alternate unit, amount, and amount unit.

    Parameters:
        NLEA_info (str): A string containing NLEA information in the format 
                         "<value> <unit> = <amount> <amount unit>".

    Returns:
        tuple[float, str, str, float, str]:
            - Value (float): The numeric value of the NLEA serving size.
            - Unit (str): The primary unit of the NLEA serving size.
            - Alternate unit (str): An alternate or cleaned version of the unit.
            - Amount (float): The numeric amount associated with the serving size.
            - Amount unit (str): The unit of the amount.

    Raises:
        ValueError: If the input string does not conform to the expected format.
    """
    
    val = None
    unit = None
    ammount = None
    for i, char in enumerate(NLEA_info):
        #check if val is set and search for first space
        if val == None:
            if char == ' ':
                val = NLEA_info[0:i]
                unitStartIndex = i+1
                continue
            else:
                continue
        if char == '=':
            unit = NLEA_info[unitStartIndex: i-1]
            ammount = NLEA_info[i+2:]
            break

    ammount, amt_unit = clean_ammount(ammount)
    return val.strip(), unit, ammount, amt_unit

def clean_unit_measure(unit: str)->tuple[str, str]:
    """
    Cleans and standardizes a unit string by removing additional information, such as text in parentheses `(info)` 
    and the word "aprx". Extracts alternate units, if present, from the parentheses.

    Parameters:
        unit (str): A string representing the unit, which may include additional information or alternate units 
                    in parentheses and the word "aprx".

    Returns:
        tuple[str, str]:
            - Cleaned unit (str): The standardized unit string with extraneous information removed.
            - Alternate unit (str): A string of alternate units extracted from the parentheses, separated by '/' 
              if multiple are found.
    """
    alt = ""
    pattern = r'\((.*?)\)'
    matches = re.findall(pattern, unit)

    if len(matches) > 1:
        for match in matches:
            alt += match + '/'
    elif len(matches) > 0:
        alt = matches[0]
    unit = unit.replace('aprx', '').strip()
    unit = unit.replace('approximate', '').strip()
    unit = re.sub(pattern, '', unit).strip()
    return unit, alt

def clean_ammount(ammount: str)->tuple[float, str]:
    """
    Cleans and parses an amount string, extracting the numeric value and its unit.

    Parameters:
        ammount (str): A string representing the amount, which typically contains a numeric value followed by a unit 
                       (e.g., "100 g" or "2.5 kg").

    Returns:
        tuple[float, str]:
            - Numeric value (float): The extracted numeric value of the amount.
            - Unit (str): The unit associated with the amount (e.g., "g", "kg").

        Returns an empty tuple ('', '') if the input string does not match the expected format.

    """
    
    pattern = r'(\d+(?:\.\d+)?)\s*(\w+)' 
    match = re.match(pattern, ammount)
    if match:
        ammount, unit = match.groups()
    else:
        return '', ''
    return ammount, unit
    
def get_unit_id(unit:str, unit_lu: pd.DataFrame)->tuple[int, pd.DataFrame]:
    """     
    Processes a unit string and returns its corresponding ID. If the unit is not found in the lookup table, 
    it adds the unit to the table with a new unique ID.

    Parameters:
        unit (str): The unit string to be processed.
        unit_lu (pd.DataFrame): A Pandas DataFrame representing the unit lookup table with the following structure:
            - 'id': A unique identifier for each unit (int).
            - 'name': The name of the unit (str).

    Returns:
        tuple[int, pd.DataFrame]:
            - ID (int): The unique identifier for the unit.
            - Updated unit_lu (pd.DataFrame): The updated unit lookup table with the unit added if it was not already present.

    Raises:
        ValueError: If the input unit is an empty string.
    """

    if unit == '':
        unit = 'g'
    
    if unit in unit_lu['name'].values:
        return int(unit_lu.loc[unit_lu['name'] == unit, 'unit_id'].values[0]), unit_lu

    next_id = 1 if unit_lu.empty else int(unit_lu['unit_id'].max() + 1)

    new_row = {'unit_id': next_id, 'name': unit}
    unit_lu.loc[len(unit_lu)] = new_row

    return next_id, unit_lu

def get_UPC(bs: BeautifulSoup)->str:
    """
    Extracts the UPC (Universal Product Code) from a BeautifulSoup object.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object containing the HTML content of the page.

    Returns:
        str: The concatenated UPC code as a string. Returns an empty string if no UPC digits are found.

    """
    rtnVal = ''
    codes = bs.find_all('div', {'class': 'upc-digit'})
    if not codes:
        return rtnVal
    
    for code in codes:
        if code.get_text():
            rtnVal += code.get_text()
    return rtnVal

def get_ingredient(bs:BeautifulSoup)->str:
    """
    Extracts the list of ingredients from a BeautifulSoup object.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object containing the HTML content of the page.

    Returns:
        str: A string of ingredients, separated by double spaces. Returns an empty string if no ingredients are found.

    Notes:
        - The function searches for a `<table>` element with the class `wide results`.
        - It retrieves all `<td>` elements with the class `left` within the table.
        - Each ingredient's text is concatenated with double spaces in the final string.
    """
    ing_list = ''
    table = bs.find('table', {'class': 'wide results'})
    if table:
        ingredients = table.find_all('td', {'class': 'left'})
    else:
        return ''
    for ing_item in ingredients:
        text = str(ing_item.get_text())
        if(text):
            ing_list += text + '  '
    
    return ing_list

def get_item_id(row: dict, items: pd.DataFrame):
    """
    Inserts a new item into the items DataFrame and returns the ID of the newly added item.

    Parameters:
        row (dict): A dictionary containing item data to be added to the DataFrame.
        items (pd.DataFrame): A Pandas DataFrame representing the items table. 
                              It is expected to have an 'id' column.

    Returns:
        tuple[int, pd.DataFrame]: 
            - The unique ID assigned to the newly added item (int).
            - The updated items DataFrame with the new row appended.

    Notes:
        - If the DataFrame is empty, the new item's ID is set to 1.
        - Otherwise, the ID is set to the current maximum ID + 1.
    """
    
    # Assign an ID to the new row
    row['item_id'] = 1 if items.empty else int(items['item_id'].max()) + 1
    row_num = len(items)
    items.loc[row_num] = row
    
    return row['item_id'], items

def get_other_measures(bs: BeautifulSoup, item_id: int, conversion_junc: pd.DataFrame, unit_lu: pd.DataFrame)->tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts additional conversion measures from a BeautifulSoup object and updates the conversion junction
    and unit lookup DataFrames.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object containing the HTML content with measure options.
        item_id (int): The ID of the item associated with the conversion measures.
        conversion_junc (pd.DataFrame): A Pandas DataFrame representing the conversion junction table.
                                        - 'id': 
                                        - 'item_id'
                                        - 'unit_id'
                                        - 'unit_alt'
                                        - 'value'
                                        - 'ammount'
                                        - 'ammount_unit'
        unit_lu (pd.DataFrame): A Pandas DataFrame representing the unit lookup table. 
                                - 'id': Unique identifier for each unit.
                                - 'name': Name of the unit.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]:
            - Updated conversion_junc (pd.DataFrame): The conversion junction table with new rows added.
            - Updated unit_lu (pd.DataFrame): The unit lookup table with any new units added.

    """
    excluded_vals = ['100 g', '1 g', '1 ounce = 28.3495 g', '1 pound = 453.592 g', '1 kg = 1000 g', 'custom g', 'custom oz']

    new_row = {'conversion_id': None, 'item_id': None, 'unit_id': None, 'unit_alt': None, 'value': None, 'unit_amt': None, 'amt_unit': None}

    measures = bs.find_all('option')

    if not measures:
        raise ValueError("Mesures total option failed")

    for measure in measures:
        if not measure:
            raise ValueError("Individual measure NONE")
        value = measure.get('value') 
        if value in excluded_vals:
            continue
        val, unit, ammount, amt_unit = split_unit_value_and_ammount(value)
        new_row['item_id'] = item_id
        new_row['unit_id'], unit_lu = get_unit_id(unit, unit_lu)
        new_row['unit_amt'] = val
        new_row['ammount'] = ammount
        new_row['amt_unit'], unit_lu = get_unit_id(amt_unit, unit_lu)
        conversion_junc = add_to_conv_junc(new_row, conversion_junc)
    
    return conversion_junc, unit_lu

def add_to_conv_junc(data: dict, conversion_junc: pd.DataFrame)->pd.DataFrame:
    """
    Adds a new row to the conversion junction DataFrame.

    Parameters:
        data (dict): A dictionary containing the data for the new row. The `id` field will be automatically assigned.
        df (pd.DataFrame): The conversion junction DataFrame to which the new row will be added.
                        It is assumed to have an 'id' column for unique identification.

    Returns:
        pd.DataFrame: The updated DataFrame with the new row appended.
    """

    data['conversion_id'] = 1 if conversion_junc.empty else conversion_junc['conversion_id'].max() + 1
    row_num = len(conversion_junc)
    conversion_junc.loc[row_num] = data
    print("Added Conv_junc data")

    return conversion_junc

def get_nutrients(bs: BeautifulSoup)->dict:
    """
    Extracts nutrient information from a BeautifulSoup object and organizes it into a dictionary.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object representing the HTML content of the page.

    Returns:
        dict: A dictionary of nutrient values in the format:
            {
                'category_name': [
                    [nutrient_name (str), alt_name (str), amount (float), unit_measure (str), daily_value (str)]
                ],
                'Calories': ['Calories', 'kcal', amount (float), 'J', '']
            }

    Raises:
        ValueError: 
            - If calorie amount cannot be accessed.
            - If a nutrient category cannot be retrieved.
    """
    nuts = {}

    nut_tables = bs.find_all('table', {'class': 'center wide cellpadding3 nutrient results'})

    cal_ammount = bs.find('td', {'id': 'calories'})

    if not cal_ammount:
        ValueError("Could Not Access Calorie Ammount")
    
    cal_ammount = cal_ammount.get_text()

    nuts['Calories'] = ['Calories', 'kcal', cal_ammount, 'J', '']

    if nut_tables:
        for nut_group in nut_tables:
            category = get_nutrient_category(nut_group)
            if not category:
                ValueError("Failed to get Nutrient Category")
            if category not in nuts.keys():
                line = parse_nutrient_table(nut_group)
                if line:
                    nuts[category] = line
                else:
                    nuts[category] = []
            else:
                nuts[category] += parse_nutrient_table(nut_group)

    return nuts

def get_nutrient_category(bs:BeautifulSoup):
    """
    Extracts the nutrient category from the provided BeautifulSoup object.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object representing the HTML content of the page.

    Returns:
        str: The name of the nutrient category if found.

    Raises:
        ValueError: If the category cannot be located in the HTML content.
    """
    cat = bs.find('th', {'colspan': '3'})
    if cat:
        return cat.get_text()
    return ValueError("Failed to Get Category")

def parse_nutrient_table(bs: BeautifulSoup):
    """
    Parses a nutrient table from the provided BeautifulSoup object and extracts nutrient information.

    Parameters:
        bs (BeautifulSoup): A BeautifulSoup object representing the HTML content of the nutrient table.

    Returns:
        list: A list of lists, where each inner list contains the following nutrient details:
            [name (str), alternate name (str), amount (float), unit (str), daily value (str)].

    Raises:
        ValueError: If nutrient name or amount cannot be retrieved.
    """
    rtnVal = []
    table_tr = bs.find_all('tr')
    if table_tr:
        for tr in table_tr:
            if tr.find('td', {'colspan': '3'}):
                continue
            if tr.find('th'):
                continue

            name = tr.find('a', {'class': 'tooltip'})
            if not name:
                name = tr.find('td', {'class': 'left'})
                if name:
                    name = name.get_text()
                else:
                    continue
            else:
                name = name.get('data-tooltip')
            alt = tr.find('span', {'class': 'gray'})
            if not alt:
                alt = ''
            else:
                alt = alt.get_text()
            ammount = tr.find('td', {'class': 'right'})
            if not ammount:
                ValueError("Failed to get Nutrient Ammount")
            ammount = ammount.get_text()
            if ammount == '':
                return None
            dv = tr.find('a', {'target': '_blank'})
            if not dv:
                dv = ''
            else:
                dv = dv.get_text()
            ammount, unit = clean_ammount(ammount)
            line_list = [name, alt, ammount, unit, dv]
            rtnVal.append(line_list)
    
    return rtnVal

def insert_nutrients(nutrient_lu: pd.DataFrame, nutrient_category_lu: pd.DataFrame, nutrient_junc: pd.DataFrame, 
                     unit_lu: pd.DataFrame, nuts: dict, item:int)->tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Inserts nutrient data into multiple lookup and junction tables, updating the nutrient, nutrient category, 
    nutrient junction, and unit lookup DataFrames.

    Parameters:
        nutrient_lu (pd.DataFrame): A Pandas DataFrame representing the nutrient lookup table. 
                                    - 'id'
                                    - 'name'
        nutrient_category_lu (pd.DataFrame): A Pandas DataFrame representing the nutrient category lookup table. 
                                            - 'id'
                                            - 'name'
        nutrient_junc (pd.DataFrame): A Pandas DataFrame representing the nutrient junction table. 
                                    - 'id':
                                    - 'item_id':
                                    - 'nutrient_id':
                                    - 'alt_id':
                                    - 'cat_id':
                                    - 'ammount'
                                    - 'unit'
                                    - 'dv'
        unit_lu (pd.DataFrame): A Pandas DataFrame representing the unit lookup table. 
                                - 'id'
                                - 'name'
        nuts (dict): A dictionary where keys are nutrient categories and values are lists of nutrient data.
                    Each nutrient data item is expected in the following format:
                    [nutrient name, alternate name, amount, unit measure, daily value].
        item (int): The ID of the item associated with the nutrients being inserted.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            - Updated nutrient_lu (pd.DataFrame): Nutrient lookup table with any new nutrients added.
            - Updated nutrient_category_lu (pd.DataFrame): Nutrient category lookup table with any new categories added.
            - Updated nutrient_junc (pd.DataFrame): Nutrient junction table with the new rows added.
            - Updated unit_lu (pd.DataFrame): Unit lookup table with any new units added.
    """

    keys = nuts.keys()

    for key in keys:
        cat_id, nutrient_category_lu = get_nutrient_category_table_id(nutrient_category_lu, key)
        if key == 'Calories':
            row_id = 1 if nutrient_junc.empty else int(nutrient_junc['nut_junc_id'].max() + 1)
            new_row, nutrient_lu, unit_lu = create_nutrient_junk_row(nuts[key], cat_id, item, row_id, nutrient_lu, unit_lu)
            nutrient_junc.loc[len(nutrient_junc)] = new_row
            continue
        data = nuts[key]
        for d in data:
            row_id = 1 if nutrient_junc.empty else int(nutrient_junc['nut_junc_id'].max() + 1)
            new_row, nutrient_lu, unit_lu = create_nutrient_junk_row(d, cat_id, item, row_id, nutrient_lu, unit_lu)
            row_num = len(nutrient_junc)
            nutrient_junc.loc[row_num] = new_row

    return nutrient_lu, nutrient_category_lu, nutrient_junc, unit_lu        

def create_nutrient_junk_row(data:list, cat:int, item:int, row_id: int, nutrient_lu:pd.DataFrame, unit_lu:pd.DataFrame)->tuple[dict, pd.DataFrame, pd.DataFrame]:
    """
    Creates a row for a nutrient junction table based on the provided data and updates the relevant lookup tables.

    Parameters:
        data (list): A list containing nutrient information in the following format:[nutrient name, alternate name, amount, unit measure, daily value].
        cat (int): The ID of the nutrient category to which this nutrient belongs.
        item (int): The ID of the item associated with this nutrient.
        row_id (int): The unique identifier for the row being created.
        nutrient_lu (pd.DataFrame):
            - 'id'
            - 'name'
        unit_lu (pd.DataFrame):
            - 'id'
            - 'name'

    Returns:
        tuple[dict, pd.DataFrame, pd.DataFrame]:
            - dict: A dictionary representing the created nutrient junction row with the following keys:
                - 'id'
                - 'item_id'
                - 'nutrient_id'
                - 'alt_id':
                - 'cat_id':
                - 'ammount':
                - 'unit':
                - 'dv':
            - Updated nutrient_lu (pd.DataFrame): The nutrient lookup table with new nutrients added, if applicable.
            - Updated unit_lu (pd.DataFrame): The unit lookup table with new units added, if applicable.

    """
    nut_junk = {'nut_junc_id': row_id, 'item_id': item, 'nutrient_id': None, 'alt_id': None, 'cat_id': cat,  'ammount': None, 'unit_id': None, 'dv': None}
    nut_junk['nutrient_id'], nutrient_lu = get_nutrient_id(nutrient_lu, data[0])
    if data[1] == '':
        nut_junk['alt_id'] = ''
    else:
        nut_junk['alt_id'], nutrient_lu = get_nutrient_id(nutrient_lu, data[1])
    nut_junk['ammount'] = data[2]
    nut_junk['unit_id'], unit_lu = get_unit_id(data[3], unit_lu)
    nut_junk['dv'] = data[4]
    return nut_junk, nutrient_lu, unit_lu
    
def get_nutrient_category_table_id(nutrient_category_lu: pd.DataFrame, cat: str)->tuple[int, pd.DataFrame]:
    """
    Retrieves the ID of a nutrient category from a lookup DataFrame. If the category does not exist, it adds the category 
    to the DataFrame with a new ID.

    Parameters:
        nutrient_category_lu (pd.DataFrame): A Pandas DataFrame representing the nutrient category lookup table. 
                                            - 'id'
                                            - 'name'
        cat (str): The name of the nutrient category to retrieve or add.

    Returns:
        tuple[int, pd.DataFrame]:
            - ID (int): The unique ID of the nutrient category.
            - Updated nutrient_category_lu (pd.DataFrame): The updated nutrient category lookup DataFrame 
            with the category added, if necessary.
    """
    if cat in nutrient_category_lu['name'].values:
        return int(nutrient_category_lu.loc[nutrient_category_lu['name'] == cat, 'cat_id'].values[0]), nutrient_category_lu
    
    next_id = 1 if nutrient_category_lu.empty else int(nutrient_category_lu['cat_id'].max()) + 1

    new_row = {'cat_id': next_id, 'name': cat}
    row_num = len(nutrient_category_lu)
    nutrient_category_lu.loc[row_num] = new_row

    return next_id, nutrient_category_lu

def get_nutrient_id(nutrient_lu: pd.DataFrame, nut:str)->tuple[int, pd.DataFrame]:
    """
    Retrieves the ID of a nutrient from a lookup DataFrame. If the nutrient does not exist, it adds the nutrient
    to the DataFrame with a new ID.

    Parameters:
        nutrient_lu (pd.DataFrame): A Pandas DataFrame representing the nutrient lookup table. 
                                    - 'id'
                                    - 'name
        nut (str): The name of the nutrient to retrieve or add.

    Returns:
        tuple[int, pd.DataFrame]: 
            - ID (int): The unique ID of the nutrient. Returns an empty string if `nut` is an empty string.
            - Updated nutrient_lu (pd.DataFrame): The updated nutrient lookup DataFrame with the nutrient added, if necessary.
    """

    if nut == '':
        raise ValueError('Nutrient_lu get id passed an empty nutrient')

    if nut in nutrient_lu['name'].values:
        return int(nutrient_lu.loc[nutrient_lu['name'] == nut, 'nutrient_id'].values[0]), nutrient_lu
    
    next_id = 1 if nutrient_lu.empty else int(nutrient_lu['nutrient_id'].max() + 1)

    new_row = {'nutrient_id': next_id, 'name': nut}
    row_num = len(nutrient_lu)
    nutrient_lu.loc[row_num] = new_row

    return next_id, nutrient_lu

def rollback_item(item_id: int, items:pd.DataFrame, conversion_junc: pd.DataFrame, nutrient_junc:pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """"""
    if item_id == None:
        return items, conversion_junc, nutrient_junc
    
    items = items[items['id'] != item_id]
    conversion_junc = conversion_junc[conversion_junc['item_id'] != item_id]
    nutrient_junc = nutrient_junc[nutrient_junc['item_id'] != item_id]

    return items, conversion_junc, nutrient_junc

def write_data(items:pd.DataFrame, unit_lu: pd.DataFrame, conversion_junc: pd.DataFrame,
               nutrient_lu:pd.DataFrame, nutrient_category_lu:pd.DataFrame, nutrient_junc:pd.DataFrame):
    """
    Writes multiple Pandas DataFrames to CSV files and prints their shapes and first few rows for inspection.

    Parameters:
        items (pd.DataFrame): A DataFrame containing item data to be saved.
        unit_lu (pd.DataFrame): A DataFrame containing unit lookup data to be saved.
        conversion_junc (pd.DataFrame): A DataFrame containing unit conversion data to be saved.
        nutrient_lu (pd.DataFrame): A DataFrame containing nutrient lookup data to be saved.
        nutrient_category_lu (pd.DataFrame): A DataFrame containing nutrient category data to be saved.
        nutrient_junc (pd.DataFrame): A DataFrame containing nutrient junction data to be saved.

    Outputs:
        - Saves each DataFrame as a CSV file in the specified directory.
    """

    global ITEMS_PATH, UNITLU_PATH, NUTLU_PATH, NUTJUNC_PATH, CONVJUNC_PATH, NUTCAT_PATH

    if os.path.exists(ITEMS_PATH):
        items_1 = pd.read_csv(ITEMS_PATH)

    if os.path.exists(CONVJUNC_PATH):
        conversion_junc_1 = pd.read_csv(CONVJUNC_PATH)
    
    if os.path.exists(NUTJUNC_PATH):
        nutrient_junc_1 = pd.read_csv(NUTJUNC_PATH)
    
    items_total = pd.DataFrame(pd.concat([items_1.iloc[:-20], items], ignore_index=True))
    conv_total = pd.DataFrame(pd.concat([conversion_junc_1.iloc[:-20], conversion_junc], ignore_index=True))
    nutrient_total = pd.DataFrame(pd.concat([nutrient_junc_1.iloc[:-20], nutrient_junc], ignore_index=True))

    items_total.to_csv(ITEMS_PATH, index=False)

    unit_lu.to_csv(UNITLU_PATH, index=False)

    conv_total.to_csv(CONVJUNC_PATH, index=False)

    nutrient_lu.to_csv(NUTLU_PATH, index=False)

    nutrient_category_lu.to_csv(NUTCAT_PATH, index=False)

    nutrient_total.to_csv(NUTJUNC_PATH, index=False)

def write_restart_data(current_letter, current_page):
    """
    Writes the current state of the script (current letter and page number) to a restart file for resuming execution later.

    Parameters:
        current_letter (str): The current letter being processed.
        current_page (int): The current page number being processed.

    Returns:
        None

    Notes:
        - The function writes the `current_letter` and `current_page` to a file named `restart.txt` in the specified directory.
        - The file is overwritten each time this function is called.
    """
    global RESTART_PATH

    with open(RESTART_PATH, 'w') as file:
        file.write(current_letter + ' ' + str(current_page))

    logging_helper.write_to_file()

def load_data_for_restart():
    """
    Loads data from multiple CSV files and initializes DataFrames for restarting the script. 
    If a file does not exist, an empty DataFrame with predefined columns is created.

    Returns:
        tuple: A tuple containing the following:
            - items (pd.DataFrame)
            - unit_lu (pd.DataFrame)
            - conversion_junc (pd.DataFrame)
            - nutrient_lu (pd.DataFrame)
            - nutrient_category_lu (pd.DataFrame)
            - nutrient_junc (pd.DataFrame)
            - restart (str)

    Notes:
        - Each CSV file is checked for existence using `os.path.exists()`.
        - If a file exists, it is loaded using `pd.read_csv()`.
        - If a file does not exist, an empty DataFrame is initialized with predefined columns.
        - The `RESTART_PATH` file is read as a plain text file to retrieve the last processed state.
    """
    global ITEMS_PATH, UNITLU_PATH, NUTLU_PATH, NUTJUNC_PATH, CONVJUNC_PATH, NUTCAT_PATH, RESTART_PATH

    if os.path.exists(ITEMS_PATH):
        items_full = pd.read_csv(ITEMS_PATH)
        items = pd.DataFrame(items_full.tail(20))
    else:
        items = pd.DataFrame(columns=['item_id', 'name', 'brand', 'NLEA_unit', 'NLEA_val', 'ammount', 'ammount_unit', 'upc', 'ingredient_list'])


    if os.path.exists(UNITLU_PATH):
        unit_lu = pd.read_csv(UNITLU_PATH)
    else:
        unit_lu = pd.DataFrame(columns = ['unit_id', 'name'])

    if os.path.exists(CONVJUNC_PATH):
        conversion_junc_full = pd.read_csv(CONVJUNC_PATH)
        conversion_junc = pd.DataFrame(conversion_junc_full.tail(20))
    else:
        conversion_junc = pd.DataFrame(columns = ['conversion_id', 'item_id', 'unit_id', 'unit_amt', 'ammount', 'amt_unit'])
    
    if os.path.exists(NUTLU_PATH):
        nutrient_lu = pd.read_csv(NUTLU_PATH)
    else:
        nutrient_lu = pd.DataFrame(columns = ['nutrient_id', 'name'])

    if os.path.exists(NUTCAT_PATH):
        nutrient_category_lu = pd.read_csv(NUTCAT_PATH)
    else:
        nutrient_category_lu = pd.DataFrame(columns = ['cat_id', 'name'])
    
    if os.path.exists(NUTJUNC_PATH):
        nutrient_junc_full = pd.read_csv(NUTJUNC_PATH)
        nutrient_junc = pd.DataFrame(nutrient_junc_full.tail(20))
    else:
        nutrient_junc = pd.DataFrame(columns = ['nut_junc_id', 'item_id', 'nutrient_id', 'alt_id', 'cat_id', 'ammount', 'unit_id', 'dv'])

    if os.path.exists(RESTART_PATH):
        with open(RESTART_PATH, 'r') as file:
            restart = file.readline()
    else:
        restart = ''
    

    return items, unit_lu, conversion_junc, nutrient_lu, nutrient_category_lu, nutrient_junc, restart
 

def main():

    global BASE_WEBSITE, FOODS_START_MOD, BRANDS_START_MOD, SITE_END, LETTER_LIST, PAGE_COUNTER

    listener_thread = threading.Thread(target=stop_listener, daemon=True)
    listener_thread.start()
    options = Options()
    options.add_argument("--headless")
    service = Service(executable_path='/snap/bin/geckodriver')

    driver = webdriver.Firefox(service=service, options=options)

    #load the data
    items, unit_lu, conversion_junc, nutrient_lu, nutrient_category_lu, nutrient_junc, restart = load_data_for_restart()
    print('Length items:\t', len(items), '\n')
    print('Length unit_lu:\t', len(unit_lu), '\n')
    print('Length conv:\t', len(conversion_junc), '\n')
    print('Length Nut_cat:\t', len(nutrient_category_lu), '\n')
    print('Length nutrient jun:\t', len(nutrient_junc), '\n')
    print('Length nutrient_lu:\t', len(nutrient_lu), '\n')

    #clean save place data
    if len(restart) > 0:
        split_restart = restart.split(' ')
        restart_letter, restart_page = split_restart[0], int(split_restart[1])
        need_restart = True
        index = LETTER_LIST.index(restart_letter)
        letter_list = LETTER_LIST[index:]
    else:
        letter_list = LETTER_LIST
        need_restart = False

    #Loop Through the letters remaining
    for letter in letter_list:
        if stop_event.is_set():
            write_data(items, unit_lu, conversion_junc, nutrient_lu, nutrient_category_lu, nutrient_junc)
            write_restart_data(letter, next_page_num)
            print("Data Has been Written, we are all set for now Exit")
            exit()

        try:
            #sets the starting page inforamtion if needs restart
            if need_restart:
                next_page_num = restart_page
                need_restart = False
            else:
                next_page_num = 1
            

            #Build the path and get the beautiful soup object
            url = BASE_WEBSITE+FOODS_START_MOD+letter+'_'+PAGE_COUNTER+str(next_page_num)+SITE_END
            bs = get_page_source(driver, url)

            #Links from current page
            #if no links are found we continue to the next letter.
            current_page_items = deque(get_table_links(bs))

            #loop through the items on the current page
            while current_page_items:
                if stop_event.is_set():
                    write_data(items, unit_lu, conversion_junc, nutrient_lu, nutrient_category_lu, nutrient_junc)
                    write_restart_data(letter, next_page_num)
                    print("Data Has been Written, we are all set for now Exit")
                    exit()


                item = deque.popleft(current_page_items)
                try:
                    url = BASE_WEBSITE + item.get('href')
                    bs = get_page_source(driver, url)

                    cur_item_id, items, unit_lu = gather_item_info(bs, items, unit_lu)

                    conversion_junc, unit_lu = get_other_measures(bs, cur_item_id, conversion_junc, unit_lu)

                    #handles the nutrient details.
                    nuts = get_nutrients(bs)
                    nutrient_lu, nutrient_category_lu, nutrient_junc, unit_lu = insert_nutrients(nutrient_lu, nutrient_category_lu, nutrient_junc, unit_lu, nuts, cur_item_id)
                    
                    cur_item_id = None
                    #if on last item try to get the next page and if no exception raised will add more links to the deque
                    if len(current_page_items) == 0:
                        next_page_num += 1
                        print("We are Still Working\nCurrent Letter:\t", letter, "\nCurrent Page:\t", str(next_page_num))
                        url = BASE_WEBSITE+FOODS_START_MOD+letter+'_'+PAGE_COUNTER+str(next_page_num)+SITE_END
                        bs = get_page_source(driver, url)
                        current_page_items.extend(deque(get_table_links(bs)))
                        
                except Exception as e:
                    tb = traceback.extract_tb(e.__traceback__)
                    print('Error:', str(e) + ' ' + str(tb[-1].name), url, e.__traceback__.tb_lineno)
                    logging_helper.add_to_log(str(e) + ' ' + str(tb[-1].name), url, e.__traceback__.tb_lineno)
                    if len(e.args) == 1:
                        print('Rolling Back Item')
                        items, conversion_junc, nutrient_junc = rollback_item(cur_item_id, items, conversion_junc, nutrient_junc)
                    if len(current_page_items) == 0:
                        next_page_num += 1
                        print("We are Still Working\nCurrent Letter:\t", letter, "\nCurrent Page:\t", str(next_page_num))
                        url = BASE_WEBSITE+FOODS_START_MOD+letter+'_'+PAGE_COUNTER+str(next_page_num)+SITE_END
                        bs = get_page_source(driver, url)
                        current_page_items.extend(deque(get_table_links(bs)))
                    continue

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            print('Error:', str(e) + ' ' + str(tb[-1].name), url, e.__traceback__.tb_lineno)
            logging_helper.add_to_log(str(e) + ' ' + str(tb[-1].name),url, e.__traceback__.tb_lineno)
            continue

    
    write_data(items, unit_lu, conversion_junc, nutrient_lu, nutrient_category_lu, nutrient_junc)
    write_restart_data(letter, next_page_num)
    print("WE HAVE FINISHED!!!!!!")
    stop_event.set()
    driver.quit()


if __name__ == '__main__':
    main()