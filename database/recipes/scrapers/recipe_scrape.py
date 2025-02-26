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
import random

options = Options()
service = Service(executable_path='/snap/bin/geckodriver')
DRIVER = webdriver.Firefox(service=service, options=options)


BASE_WEBSITE = 'https://www.allrecipes.com/'
WEBSITE_CATEGORIES = ['recipes-a-z-6735880', 'ingredients-a-z-6740416', 'cuisine-a-z-6740455']
WEBSITE_ALT_CATEGORIES = ['recipes/85/holidays-and-events/', 'recipes/17562/dinner/']
RECIPE_TAGS_PATH = '/home/bg-labs/bg_labs/fms/database/recipes/data/tags_lu.csv'

TAGS_LU_COLUMNS = ['id', 'tag', 'href']
TAG_JUNC_COLUMNS = ['id', 'tag_id', 'recipe_id']

stop_event = threading.Event()

def stop_listener():
    """
    Behavior:
    - Waits for the user to press the Enter key.
    - Prints a message indicating the script is stopping and requests patience during the cleanup process.
    - Sets a shared `stop_event` flag, signaling the main script to stop.
    """
    input("Press Enter to Stop the script...\n")
    print("Stopping the Recipe Gather...Please be patient while we clean up you will be notified when it is safe to close")
    stop_event.set()

def get_page_source(url: str)->BeautifulSoup:
    """"""
    global DRIVER

    try:
        DRIVER.get(url)
        bs = BeautifulSoup(DRIVER.page_source, 'html.parser')
        return bs
    except:
        error = "Can't Reach URL:\t" + url
        print(error)

def gather_list_of_tags():
    """Gathers all of the 'Types' links if the file does not exist"""
    global TAGS_LU_COLUMNS, DRIVER, WEBSITE_CATEGORIES, BASE_WEBSITE, WEBSITE_ALT_CATEGORIES, RECIPE_TAGS_PATH

    types = pd.DataFrame(columns=TAGS_LU_COLUMNS)

    for cat in WEBSITE_CATEGORIES:
        try:
            url = BASE_WEBSITE + cat  
            bs = get_page_source(url)

            types_raw = bs.find_all('a', {'class': 'mntl-link-list__link text-body-100 global-link text-body-100 global-link'})

            types = pd.concat([types.copy(), build_tags_lu_df(types_raw)])

        except Exception as e:
            continue

    for cat in WEBSITE_ALT_CATEGORIES:
        try:
            url = BASE_WEBSITE + cat
            bs = get_page_source(url)

            types_raw = bs.find_all('a', {'class': 'mntl-taxonomy-nodes__link mntl-text-link text-label-300 global-link'})

            types = pd.concat([types.copy(), build_alt_tags_df(types_raw)])
        except:
            continue
    
    types['id'] = range(1, len(types)+1)

    types.to_csv(RECIPE_TAGS_PATH, index=False)

    return types
        
def build_tags_lu_df(types_raw: BeautifulSoup)->pd.DataFrame:
    """"""
    global TAGS_LU_COLUMNS

    df = pd.DataFrame(columns=TAGS_LU_COLUMNS)
    new_row = {TAGS_LU_COLUMNS[0]: None, TAGS_LU_COLUMNS[1]: None, TAGS_LU_COLUMNS[2]: None}

    
    for type in types_raw:
        try:
            new_row['tag'] = type.get_text().strip()
            new_row['href'] = str(type.get('href')).strip()
            row_num = len(df)
            new_row['id'] = 1 if row_num == 0 else row_num
            df.loc[row_num] = new_row
        except Exception as e:
            print('Failed to get tag or href from Category BS object\n' + str(type) + '\n')
            continue

    return df

def build_alt_tags_df(types_raw: BeautifulSoup)->pd.DataFrame:
    """"""
    global TAGS_LU_COLUMNS

    df = pd.DataFrame(columns=TAGS_LU_COLUMNS)
    new_row = {TAGS_LU_COLUMNS[0]: None, TAGS_LU_COLUMNS[1]: None, TAGS_LU_COLUMNS[2]: None}

    for type in types_raw:
        try:
            new_row['href'] = type.get('href')
            text = type.find_next('span', {'class': 'link__wrapper'})
            new_row['tag'] = text.get_text()
            row_num = len(df)
            new_row['id'] = 1 if row_num == 0 else row_num
            df.loc[row_num] = new_row
        except:
            print('Failed to get href/tag:\n' + str(type))
            continue

    return df

def open_tags_lu()->pd.DataFrame:
    """"""
    if os.path.exists(RECIPE_TAGS_PATH):
        return pd.read_csv(RECIPE_TAGS_PATH)
    else:
        return gather_list_of_tags()

def write_tags_lu(tags_lu:pd.DataFrame):
    global RECIPE_TAGS_PATH
    tags_lu.to_csv(RECIPE_TAGS_PATH, index=False)

def select_random_from_DF(data: pd.DataFrame)->int:

    return random.randint(0, len(data) - 1)

def get_new_tags(bs:BeautifulSoup)->list[dict]:
    """"""
    tagList = []
    crumbTrail = bs.find('ul', {'class': 'comp mntl-universal-breadcrumbs mntl-block text-label-300 breadcrumbs'})
    tagBlock = bs.find('ul', {'class': 'comp mntl-taxonomy-nodes__list mntl-block'})
    crumbTrailLinks = crumbTrail.find_all('a')
    blockLinks = tagBlock.find_all('a')
    if crumbTrailLinks:
        for crumb in crumbTrailLinks:
            tagRow = {'id': '', 'tag': '', 'href': ''}
            name = crumb.find('span').get_text()
            if name:
                if name == 'Recipes':
                    continue
                if name.endswith('Recipes'):
                    name = name[:-7]
                tagRow['tag'] = name.strip()
                tagRow['href'] = crumb.get('href').strip()
                tagList.append(tagRow)
    if blockLinks:
        for link in blockLinks:
            tagRow = {'tag': '', 'href': ''}
            name = link.find('span').get_text()
            if name:
                tagRow['tag'] = name.strip()
                tagRow['href'] = link.get('href').strip()
                tagList.append(tagRow)

    return tagList
                
def add_new_tags(tagList: list[dict], tags_lu: pd.DataFrame)->pd.DataFrame:
    """"""
    for tag in tagList:
        if tags_lu[(tags_lu['tag'] == tag['tag'])]:
            continue
        else:
            id = len(tags_lu)
            tag['id'] = id
            tags_lu.loc[len(tags_lu)] = tag

    return tags_lu

def get_card_links(bs:BeautifulSoup)->list[BeautifulSoup]:
    """"""
    links = bs.find_all('a', {'class': 'comp mntl-card-list-items mntl-universal-card mntl-document-card mntl-card card card--no-image'})
    if links:
        return links
    else:
        raise ValueError("Failed to Get Card Link List")

def get_article_links(cards:BeautifulSoup)->list[str]:
    """"""
    articleCards = []
    for card in cards:
        favButton = card.find('button', {'class', 'mm-myrecipes-favorite__link'})
        if favButton:
            continue
        try:
            articleCards.append(card.get('href'))
        except:
            continue

    if len(articleCards) == 0:
        raise ValueError("Failed to pull any Article Links")
    
    return articleCards

def get_recipe_links_from_article(bs:BeautifulSoup)->list[str]:
    """"""
    recipeLinks = bs.find_all('a', {'class': 'mntl-sc-block-universal-featured-link__link mntl-text-link button--contained-standard text-label-300'})
    recipeHref = []
    if recipeLinks:
        for link in recipeLinks:
            recipeHref.append(link.get('href'))
    else:
        raise ValueError('Failed to get Recipe Links From Article')

    return recipeLinks

def get_tag_id(tag:str, tag_lu)

def create_recipe_tag_rows(newTags:list[str], tag_lu:pd.DataFrame)->list[dict]:
    """"""
    tagJuncRow = {'id', 'tag_id', 'recipe_id'}
    get_tag_id()

def main():
    
    global BASE_WEBSITE, DRIVER, RECIPE_TAGS_PATH

    recipeRow = {'recipe_id', 'name', 'servings', 'yeild' 'href'}
    ingredientJuncRow = {'id', 'item_id', 'recipe_id', 'unit_id', 'unit_amt', 'grouping'}
    timingLuRow = {'timeing_id', 'name'}
    timeingJuncRow = {'id', 'recipe_id', 'timeing_id', 'duration'}
    methodsRow = {'method_id', 'step', 'instruction'}
    methodJuncRow = {'id', 'method_id', 'recipe_id'}
    tagsJuncRow = {'id', 'tag_id', 'recipe_id'}



    listener_thread = threading.Thread(target=stop_listener, daemon=True)
    listener_thread.start()

    tags_lu = open_tags_lu()

    bs = BeautifulSoup()

    while not stop_event.is_set():
        tagNum = select_random_from_DF(tags_lu)
        tagURL = tags_lu['href'].iloc[tagNum]
        try:
            bs = get_page_source(tagURL)
            if bs:
                try:
                    newTags = get_new_tags(bs)
                    tags_lu = add_new_tags(newTags, tags_lu)
                except Exception as e:
                    print("Error Gathering New Tags:", e, "\nURL:", tagURL)
                    logging_helper.add_to_log("Error Gathering New Tags: " + e,tagURL, 'NA')

                try:
                    cardLinks = get_card_links(bs)
                    articleCards = get_article_links(cardLinks)
                except:
                    print("Error Gathering Card Link:", e, "\nURL:", tagURL)
                    logging_helper.add_to_log("Error Gathering Card Links: " + e,tagURL, 'NA')
                    continue

                for article in articleCards:
                    try:
                        bs = get_page_source(article)
                        recipeLinks = get_recipe_links_from_article(bs)
                    except:
                        print("Error Gathering Recipe Links:", e, "\nURL:", article)
                        logging_helper.add_to_log("Error Gathering Recipe Links: " + e, article, 'NA')
                        continue
                for recipe in recipeLinks:
                    try:
                        bs = get_page_source(recipe)
                        newTags = get_new_tags(bs)
                        tags_lu = add_new_tags(newTags, tags_lu)
                        #build recipe row
                        #build tag junc row(s)
                        #build times junc row(s)
                        #build ingredient rows
                        #build method rows
                        #add all rows to data frames
                    except:
                        print('Failed on Recipe Page Gather:', e, recipe, 'N/A' )


        except Exception as e:
            print("Error:", e)
            continue
        
    write_tags_lu(tags_lu)



if __name__ == '__main__':
    main()