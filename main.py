import pathlib, textwrap, os, sys
from PIL import Image

img = Image.open('image.jpeg')

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

from IPython.display import display
from IPython.display import Markdown

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

## Text to Text
# model = genai.GenerativeModel('gemini-pro')

# print(model.generate_content(input("Enter prompt: ")).text)

# ## Text to Text but streaming
# model = genai.GenerativeModel('gemini-pro')

# response = model.generate_content(input("Enter prompt: "), stream=True)
# for chunk in response:
#    print(chunk.text, end='')

# print()
# # print(response.prompt_feedback)

## Gemini Pro Vision
# model = genai.GenerativeModel('gemini-pro-vision')

# response = model.generate_content(
#     [
#         'Write a short, engaging blog post based on this picture. It should describe the picture and have a three-act storytelling structure.',
#         img
#     ],
#     stream=True
# )
# for chunk in response:
#     print(chunk.text, end='')

## Customising Advanced Generation Config
# model = genai.GenerativeModel('gemini-pro')

# response = model.generate_content(
#     'Tell me a coming-of-age three-act narrative story about a boy who finds a magic backpack.',
#     generation_config=genai.types.GenerationConfig(
#         candidate_count=1,
#         stop_sequences=['Act 3'],
#         max_output_tokens=1000,
#         temperature=1.0
#     ),
#     stream=True
# )

# for chunk in response:
#     print(chunk.text, end='')

## Chat conversations
model = genai.GenerativeModel('gemini-pro')

chat = model.start_chat(history=[])

prompt = None
while prompt != ".exit":
    prompt = input("You: ")
    response = chat.send_message(prompt, stream=True)
    print()
    print("AI: ", end='')
    for chunk in response:
        print(chunk.text, end='')
    print()
    print()

chat.history[0].parts[0].text