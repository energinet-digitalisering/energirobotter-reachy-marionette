import os

import bpy
import openai


class ActionsGPT():

    def __init__(self):

        self.client = None
        self.api_key = None

        self.chat_history = []

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
                {'ERROR'}, "OPENAI_API_KEY environment variable must be set.")
            return

        print(os.getenv("OPENAI_API_KEY"))

        try:
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        except:
            report_function(
                {'ERROR'}, "No API key detected. Please write API key to OPENAI_API_KEY environment variable.")
            return False

        return True

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
        messages.append(self.chat_history[-10:])

        # Add user promt
        message_user = {"role": "user", "content": promt}
        messages.append(message_user)
        self.chat_history.append(message_user)

        # Request response from ChatGPT
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
        )

        # print(response.choices[0].message)

    def print_actions(self, reachy_object, report_function):
        for action in bpy.data.actions:
            print(action.name)

        bpy.context.object.animation_data.action = bpy.data.actions.get(
            "ReachyShrug")

        reachy_object.animate_angles(report_function)
