init python:
    import json
    import openai
    import os
    import random
    import requests
    import math
    import time
    import base64
    import io


    with open(config.basedir + "/game/assets/prompts/prompt_templates.json", "r") as f:
        prompt = json.load(f)

    retrycount = 3

    class AIManager():
        def __init__(self, character_name, chathistory, full_path, resume=False):
            self.character_name = character_name
            self.chathistory = chathistory
            self.full_path = full_path
            self.resume = resume
            self.NARRATION = False
            self.rnd = random.randint(1,7)
            self.retrying = False
            self.dbase = Data(path_to_user_dir=self.full_path)

        @staticmethod
        def context_to_progress_story(msg):
            rng = random.randint(1,3)
            context = ""

            with open(f"{config.basedir}/game/assets/prompts/progress_story.json") as f:
                structs = json.load(f)
            if rng == 1:
                context += structs["1"]
            elif rng == 2:
                context += structs["2"]
            elif rng == 3:
                context += structs["3"]

            return msg + context



        def get_char_name(self, aireply):
            # WIP method that should be used when multiple
            # characters are speaking
            if "[CHAR]" in aireply:
                pass    
            return self.character_name



        def controlMood(self, face, body):
            """Display different facial expressions"""
            if not face or not body: return

            char_name = Configs().characters[self.character_name.title()]
            full_sprite_emotions = char_name["full_sprites"] # dont render "left" or "right" body sprites if head_sprite returns smthing from this list
            head_sprite = char_name["head"]
            leftside_sprite = char_name["left"]
            rightside_sprite = char_name["right"]


            for h in head_sprite:
                if h == face.lower():
                    self.dbase.updateSceneData("head_sprite", head_sprite[h])

                    if h in full_sprite_emotions:
                        self.dbase.updateSceneData("left_sprite", char["none"])
                        self.dbase.updateSceneData("right_sprite", char["none"])
                        return

            if head_sprite in full_sprite_emotions:
                self.dbase.updateSceneData("left_sprite", char["none"])
                self.dbase.updateSceneData("right_sprite", char["none"])
                return


            for l in leftside_sprite:
                if body == body.lower():
                    self.dbase.updateSceneData("left_sprite", leftside_sprite[l])

            for rr in rightside_sprite:
                if rr == body.lower():
                    self.dbase.updateSceneData("right_sprite", rightside_sprite[rr])




        def controlBackground(self, scene):
            """Display different background image"""
            if not scene: return

            bg_scenes = Configs().bg_scenes
            for key in ('default', 'checks'):
                if scene in bg_scenes[key]:
                    return self.dbase.updateSceneData("background", bg_scenes[key][scene])
            return self.dbase.updateSceneData("background", bg_scenes['checks']["clubroom"])





        def removeKeywords(self, reply):
            """Get rid of keywords and return a clean string"""

            def getContent(start, end, reply=reply):
                try:
                    content = reply.split(start)[1].split(end)[0].strip()
                    return content
                except IndexError:
                    return None
                except AttributeError:
                    return None

            char = getContent('[CHAR]', '[CONTENT]')
            face = getContent('[FACE]', '[BODY]')
            body = getContent('[BODY]', '[CONTENT]')
            scene = getContent('[SCENE]', '[NARRATION]')

            reply = reply.replace('[END]', '')

            if "[CONTENT]" in reply:
                reply = reply.split("[CONTENT]")[1].strip()
            elif "[NARRATION]" in reply:
                reply = reply.split("[NARRATION]")[1].strip()
            else:
                # Typically this means that the model didnt return a proper content field
                reply = "ERROR"

            return reply, char, face, body, scene



        def removePlaceholders(self):
            """remove placeholders in json files"""
            raw_examples = Info().getExamplePrompts[f"gpt4_{self.character_name}"]

            bg_scenes = [s for s in Configs().bg_scenes["default"]] + [s for s in Configs().bg_scenes["checks"]]
            emotions = ', '.join([e for e in Configs().characters[self.character_name.title()]['head']])
            backgrounds = ', '.join(bg_scenes)
            

            string = raw_examples[0]['content'].replace("<name>", persistent.playername)
            string = string.replace("<char>", self.character_name)
            string = string.replace("<emotions>", emotions)
            string = string.replace("<backgrounds>", backgrounds)

            string = raw_examples[0]['content'] = string
            raw_examples[0]['content'] = string


            return raw_examples




        def retryPrompt(self, chathistory, reply, current_emotion, current_body):
            """If the generated response doesnt use the emotions specified in the characters.json list
            eg. '[FACE] super shy' then remind the ai to only use what's in
            the list and redo the response
            """
            if current_emotion and current_body:
                if (reply.startswith("[FACE]")) and (current_emotion not in Configs().characters[self.character_name.title()]["head"]) or ("explain" not in current_body and "relaxed" not in current_body):
                    print("<<retrying>>")
                    self.chathistory[f"gpt4_{self.character_name}"].pop()
                    return True
            return False



        def ai_response(self, userInput):
            """Gets ai generated text based off given prompt"""
            self.rnd = random.randint(1,7)
            if "(init_end_sim)" in userInput and self.character_name == "monika":
                self.dbase.updateSceneData("zone", "zone")
                return '...'

            emotions = ', '.join([e for e in Configs().characters[self.character_name.title()]['head']])
            reminder = "" if self.retrying == False else Info().getReminder[self.character_name.lower()]["emotes"].replace("<emotes>", emotions)

            # Log user input
            examples = self.removePlaceholders()
            self.chathistory.append({"role": "user", "content": userInput + reminder})
            response = openai.ChatCompletion.create(
                model="gpt-4-1106-preview",
                messages=examples + self.chathistory,
                temperature=0.6,
                max_tokens=90
                )


            # Log AI input
            reply = response = response.choices[0].message.content
            self.chathistory.append({"role": "assistant", "content": response})
            reply, _, face, body, scene = self.removeKeywords(reply)


            # If the AI responds w/ an emotion/body not listed, redo the response
            global retrycount
            self.retrying = self.retryPrompt(self.chathistory, response, face, body)
            if self.retrying:
                retrycount -= 1
                if retrycount <= 0:
                    self.retrying = False
                    retrycount = 3
                else:
                    return self.ai_response(userInput)

            self.controlMood(face, body)
            self.controlBackground(scene)


            #TODO Should only run if player has voice enabled
            if self.NARRATION != True:
                #self.char_speaks(final_res, emote=emote)
                pass


            with open(f"{self.full_path}/chathistory.json", 'w') as f:
                json.dump(self.chathistory, f, indent=2)
            return reply


