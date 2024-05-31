import os
from requests.exceptions import RequestException

import bpy
import openai


class ActionsGPT():

    def __init__(self):

        self.client = None
        self.api_key = None
        self.chat_history = []

        self.gpt_model = "gpt-4o"
        self.max_tokens = 1000

        self.system_prompt = """"
            You are a humanoid robot named Reachy. You can emote using the actions ReachyWave, ReachyDance, ReachyYes, ReachyNo, and ReachyShrug.

            - Respond to user input with the most appropriate action's name.
            - If no other action is more appropriate, use ReachyShrug.

            Example:

            user: Hello Reachy
            assistant: ReachyWave
            """

    def activate(self, report_function):

        if not os.getenv("OPENAI_API_KEY"):
            report_function(
                {'ERROR'}, "No API key detected. Please write API key to OPENAI_API_KEY environment variable. System restart may be required after writing to environment variable.")
            return False

        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        return True

    def get_gpt_response(self, messages, report_function):

        try:
            # Request response from ChatGPT
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=messages,
                max_tokens=self.max_tokens,
            )

            if hasattr(response, "choices") and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                report_function({"ERROR"}, "No completion choices returned.")
                return "Sorry, I couldn't generate a response."

        except openai.OpenAIError as error:
            report_function({"ERROR"}, "OpenAI API error: " + str(error))
            return "Sorry, there was an error with the AI service."

        except RequestException as e:
            report_function({"ERROR"}, "Request error: " + str(error))
            return "Sorry, there was a network issue."

        except Exception as error:
            report_function({"ERROR"}, "Could not send response: " + str(error))
            return "Sorry, something went wrong."

    def send_request(self, promt, reachy_object, report_function):

        if reachy_object.reachy == None:
            report_function({'ERROR'}, "Reachy not connected!")
            return

        if len(promt) == 0:
            report_function(
                {'ERROR'}, "Please provide a promt.")
            return

        if not self.client:
            report_function(
                {'ERROR'}, "No OpenAI client detected. Please activate client.")
            return

        # Add system promt and recent chat history
        messages = [{"role": "system", "content": self.system_prompt}]
        # messages.extend(self.chat_history[-10:]) # Uncommented for now, history does not provide extra context

        # Add user promt
        message_user = {"role": "user", "content": promt}
        messages.append(message_user)
        self.chat_history.append(message_user)

        # Get response from ChatGPT, and send action / animation to Reachy
        response = self.get_gpt_response(messages, report_function)
            report_function(
                {'ERROR'}, "Could not send response: " + str(error))
            return

        # Get action from response, and send animation to Reachy
        action = response.choices[0].message.content

        report_function({'INFO'}, "Chosen action: " + action)

        bpy.context.object.animation_data.action = bpy.data.actions.get(action)
        reachy_object.animate_angles(report_function)
