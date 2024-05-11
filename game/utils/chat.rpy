init python:
    import asyncio
    import json
    import random
    import os
    import io


    class SetupChat:
        def __init__(self, chat_name, character_name):
            self.chat_name = chat_name
            self.character_name = character_name
            self.path_to_user_dir = f"{config.basedir}/chats/"
            self.tools = Tools(self.path_to_user_dir)
            self.scenedata_default = {
                                "gamemode": "none",
                                "music": "none",
                                "background": "",
                                "character": "",
                                "head_sprite": "",
                                "left_sprite": "",
                                "right_sprite": "",
                                "zone": ""
                            }

            with open(f"{config.basedir}/game/assets/prompts/prompt_templates.json") as f:
                self.prompt_template = json.load(f)




        def setup(self):
            chathistory = []

            # If the "chats" folder doesn't exist, create it.
            if not os.path.exists(self.path_to_user_dir):
                os.makedirs(self.path_to_user_dir, mode=0o777)

            userInput = "{RST}"

            full_path = self.tools.createRealm(name_of_realm=self.chat_name, scenedata_default=self.scenedata_default)
            #chathistory = self.tools.checkFile(chathistory)
            #return self.chat(userInput=userInput, chathistory=chathistory)
            return full_path


        def chat(self, path, chathistory=[], userInput="{RST}"):
            msg = AIManager(
                character_name=self.character_name,
                full_path=path,
                chathistory=chathistory
                ).ai_response(userInput)


            return msg



    class Tools:
        def __init__(self, path_to_user_dir):
            self.path_to_user_dir = path_to_user_dir


        def checkFile(self, chathistory):
            try:
                with open(self.path_to_user_dir + f"/chathistory.json", 'r') as f:
                    chathistory = json.load(f)
                    return chathistory
            except FileNotFoundError:
                with open(self.path_to_user_dir + f"/chathistory.json", 'w') as f:
                    json.dump([], f, indent=2)
            return chathistory




        def createRealm(self, name_of_realm, scenedata_default):
            """Creates specific folder in `chats` to store all
            realms.
            """
            path = self.path_to_user_dir + name_of_realm
            full_path = ""

            i = 1
            while True:
                full_path = f"{path}_{i}"
                if not os.path.exists(full_path):
                    os.makedirs(full_path, mode=0o777)
                    break
                else:
                    i += 1


            with open(full_path + "/scenedata.json", 'w') as f:
                json.dump(scenedata_default, f, indent=2)


            with open(full_path + f"/chathistory.json", 'w') as f:
                json.dump([], f, indent=2)

            # Metadata for chats
            metadata_default = {
                "chats": []
            }
            metadata_path = f"{config.basedir}/chats/metadata.json"
            if not os.path.exists(metadata_path):
                with open(metadata_path, 'w') as f:
                    json.dump(metadata_default, f, indent=2)

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            metadata["chats"].append(
                {
                    "name": name_of_realm,
                    "note": "-",
                    "character": "",
                    "gamemode": "none"
                }
            )

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            return full_path
