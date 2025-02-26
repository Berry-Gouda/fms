from bs4 import BeautifulSoup
import urllib.request
import re

class Recipe():

    def __init__(self):
        self.name = ''
        self.url = ''
        self.ingredients = []
        self.methode = []
        self.pictureURL = ''
        self.mealType = ''
        self.tags = []
        self.prepTime = 0
        self.cookTime = 0
        self.freezeTime = 0
        self.servings = 0
        self.rating = 0

class Website():

    def __init__(self, name: str, url: str):

        self.name = name
        self.url = url


class RecipeCrawler():

    def __init__(self, site: Website):
        self.startingURL = site.url
        self.currentURL = site.url

    def get_starting_url_html(self):
        bs = BeautifulSoup(urllib.request.urlopen(self.currentURL), 'html.parser')
        self.currentURL = self.startingURL
        print(bs)

    def gather_all_links(self):

        spotlightLinks = []
        categoryLinks = self.get_category_links()
        
        print("We Have " + str(len(categoryLinks)) + " Category Links")

        for cat in categoryLinks:
            print("Headed To: " + cat)
            for link in self.get_spotlight_links(cat):
                if link in spotlightLinks:
                    continue
                else:
                    spotlightLinks.append(link)
            
            print("Current Total Reciple Links Size: " + str(len(spotlightLinks)))


    def get_category_links(self)->[]:
        bs = BeautifulSoup(urllib.request.urlopen(self.currentURL), 'html.parser')
        raw_links = bs.find_all('a', {'class': 'link-list__link type--dog-bold type--dog-link'})
        
        cleanedLinks = []
        for link in raw_links:
            cleanedLinks.append(link.attrs['href'])

        return cleanedLinks
    
    def get_spotlight_links(self, url:str)->[]:

        bs = BeautifulSoup(urllib.request.urlopen(url), 'html.parser')
        recipe_links = bs.find_all('a', {'class': 'comp mntl-card-list-items mntl-document-card mntl-card card card--no-image'})

        pattern = r'\/article\/'

        cleaned_links = []
        
        for link in recipe_links:
            linkURL = link.attrs['href']
            if re.search(pattern, linkURL):
                continue
            else:
                cleaned_links.append(linkURL)

        return cleaned_links
    
    def gather_recipe_info(self, url:str):
        
        temp = Recipe()
        bs = BeautifulSoup(urllib.request.urlopen(url), 'html.parser')
        temp.url = url
        temp.name = bs.find('h1', {'id': 'article-heading_1-0'}).get_text()
        rawIngredients = bs.find('ul', {'class': 'mntl-structured-ingredients__list'}).find_all('p')
        rawMethod = bs.find_all('p', {'class': 'comp mntl-sc-block mntl-sc-block-html'})
        temp.pictureURL = bs.find('img', {'class': re.compile(".*primary-image.*")}).attrs['src']
        

        counter = 0

        for item in rawIngredients:
            temp.ingredients.append(item.get_text())

        for item in rawMethod:
            temp.methode.append(item.get_text())

        print(temp.name)
        print(temp.url)
        print(temp.ingredients)
        print(temp.methode)
        print(temp.pictureURL)
            





def main():

    allRecipes = Website("All Recipes", "https://www.allrecipes.com/recipes-a-z-6735880")
    sites = [allRecipes]

    

if __name__ == "__main__":
    main()