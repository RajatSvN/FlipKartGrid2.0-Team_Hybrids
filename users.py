import experiment
import pprint

response = experiment.main_function({
    "website_name": "myntra.com",
    "keywords_array": ["tshirt", "t-shirt", "t_shirt"],
    "banned_keywords_array": ["sweatshirt"],
    "num_images": 5,
    "num_product_urls": 2
})

# number of requests to VISION API -> (num_images * num_product_urls)

pp = pprint.PrettyPrinter()
pp.pprint(response)




