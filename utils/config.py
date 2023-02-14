import yaml


# create a config class
class Config:
    # create a function to load config
    def load_config(self):
        # load config from yaml file
        with open("config.yaml", "r") as file:
            # load config
            config = yaml.load(file, Loader=yaml.FullLoader)
            # return config
            return config
