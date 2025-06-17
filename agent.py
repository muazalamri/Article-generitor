from json import load
import json
import asyncio
import requests
import logging
# Configure the API key for Google Generative AI
api_key="API"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def gen(prompt,api_key=api_key):
    try:
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # Check for HTTP errors
        if not response.ok:
            logging.error(f"API request failed with status {response.status_code}: {response.text}")
            return None

        data = response.json()
        
        # Safely access nested dictionary keys
        try:
            content = data['candidates'][0]['content']['parts'][0]['text']
            return content
        except (KeyError, IndexError) as e:
            logging.error(f"Unexpected response structure: {str(e)}")
            logging.debug(f"Full response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Network/connection error occurred: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return None

# Example usage:
# if __name__ == "__main__":
#     main("your_api_key_here")

class Asseten:
    def __init__(self, name: str = 'asseten', genfun=gen):
        self.name = name
        self.genfun = gen
        self.requests = {}
        self.counter = 0

    def new_request(self, id, prompt):
        self.counter += 1
        self.requests[id] = {}
        self.requests[id]['prompt'] = prompt

    async def send_to_db(self, id):
        # add_to_db(Response, **self.requests[id])
        self.requests.pop(id, '')

    async def detect_user_entity(self, id):
        self.requests[id]['UE'] = await self.genfun(
            f"study this prompt and detect user entity in only one sentence: {self.requests[id]['prompt']}\nexamples:\n'write me a story':'user want a english story',\n'hello':'user is greeting he want me to answer him',"
        )
        return {'status':'done'}

    async def detect_needed_data(self, id):
        self.requests[id]['ND'] = await self.genfun(
            f"study this prompt and detect needed data as a list of informaition: {self.requests[id]['prompt']}.\nnote if data is not enough return genral data.\nreturn information only with qutitions."
        )
        return {'status':'done'}

    async def topicer(self, title):
        text = await self.genfun(
            f"study this title and suggest a list of 100 topics that they are realated to it and new and seo optimized and inter-reseting\ntitle:{title}.\nreturn a list like this:\ntopic1.\ntopic2.\ntopic3.write topic list only and no more.\ntitles must be in same language to given title.")
        return text
    async def planer(self, id):
        self.requests[id]['STRdes'] = await self.genfun(f'study tis prompt and descid if it is complex(coding math sinctifcal quize or some thing need thinking) answer with True else if it not compelx(greeting ask about name your self or want a joke or story) answer with False,you answer must be True or False only,promt"{self.requests[id]["prompt"]}"')
        self.requests[id]['des'] =True if 'T' in self.requests[id]['STRdes'] else False
        if (self.requests[id]['des']):
            await self.detect_user_entity(id)
            await self.detect_needed_data(id)
            self.requests[id]['plan'] = await self.genfun(
            f"you are ai asseten, I will provide you with prompt, user entity, needed data your task to make a step by step plan to do the task it make steps in shape of list: prompt:{self.requests[id]['prompt']},\nuser entity: {self.requests[id]['UE']},\nneed data: {self.requests[id]['ND']}"
            )
        return {'status':'done'}
    

    def style_to_json(self, id):
        return load(self.requests[id]['new_style'])
    
    async def answer(self, prompt):
        userId = 1
        id = str(self.counter)
        self.new_request(str(self.counter), prompt)
        await self.planer(id)
        if (self.requests[id]['des']):
            self.requests[id]['task'] = await self.genfun(
                f"you are expered prompt engeneer ,your task is to write a prompt to ai model to do the plan as user enity work if the prompt is comlex but if it is dircet like greeting,thanking,asking about name tell the model to give basic answer for it in one and if user asked you to change some thing in page style say to him it is done.sentence \nprompt:{self.requests[id]['prompt']}, spicify the expected out put language and write prompt in the excpected out put language then give the model instrucation to have excpected out put instrucation ,ai most answer what ever happened ,it can give some suggestion on the last line.\nplan:{self.requests[id]['plan']},\nuser entity:{self.requests[id]['UE']}.\ensttraction of answer:\n.answer must be lovly and lovful.\n.answer must not contain useless data.\n.of the task is diffecalt make it esyer."
            )
        else:self.requests[id]['task']=self.requests[id]['prompt']
        self.requests[id]['answer'] = await self.genfun(self.requests[id]['task'])
        #await self.detect_user_filling(id, userId)
        await self.recustom(id)
        return (self.requests[id])
asset=Asseten()


from flask import render_template,Flask,request
import asyncio
app=Flask(__name__)
  
async def AItopicer(prompt):
    print('prompt--------->',prompt)
    text=await asset.topicer(prompt) 
    return {'res':text}

@app.route('/',methods=['GET','POST'])
def my_blog():
    if request.method=="GET":
        return render_template('mange.html')
    data = asyncio.run(AItopicer(request.form.get('topic')))['res'].replace('\n','<br>')
    open('topic/'+request.form.get('topic')+'.txt','w',encoding='utf-8').write(data)
    data=(data[data.index(':')+1:].split('<br>'))
    data=['<div class="btn btn-primary">'+i+'</div>' for i in data if i!='']
    data='<br><br>'.join(data)
    return render_template('mange.html').replace('titles will be here',data)
app.run()