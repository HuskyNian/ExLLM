import os
import requests
from openai import AzureOpenAI,OpenAI
import time
#from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential, get_bearer_token_provider
def AzureCliCredential():
    pass
def ChainedTokenCredential():
    pass
def DefaultAzureCredential():
    pass
def get_bearer_token_provider():
    pass
# import google.generativeai as genai
class LLM:
    def __init__(self,model='chatgpt',config=None):
        
        print(f'using model: {model}')
        self.model_choice = model
        if ',' in model:
            self.model_choice = model.split(',')[1]
            self.chat = self.proxy_chat
        else:
            self.model = self._init_model(model)
            self.chat = self._init_chat(model)
        print('model choice:',self.model_choice)
        self.input_tokens = 0
        self.output_tokens = 0
        self.config = config
        self.t = self.config.get('model.temperature',default=None)

    def proxy_chat(self,content):
        base_url = "http://35.220.164.252:3888/v1/chat/completions"
        api_key = os.getenv("MY_API_KEY") 
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"  
        }
        
        if self.t is not None:
            data = {
                "model": self.model_choice, # 可以替换为需要的模型
                "messages": [
                    {"role": "user", "content": content}
                ],
                
                "temperature": self.t # 自行修改温度等参数
            }
        else:
            data = {
                "model": self.model_choice, # 可以替换为需要的模型
                "messages": [
                    {"role": "user", "content": content}
                ],
                
            }
        while True:
            try:
                response = requests.post(base_url, headers=headers, json=data)
                response.raise_for_status()  
                if response.status_code != 200:
                    print(f"Request failed with status code {response.status_code}")
                    print("Response headers:", response.headers)
                    try:
                        # 尝试解析 JSON 返回
                        print("Response JSON:", response.json())
                    except Exception:
                        # 如果不是 JSON，就直接打印文本
                        print("Response text:", response.text)
                else:
                    break
            except Exception as e:
                print(f'Exception {e},retry in 20s')
                time.sleep(5)
        response = response.json()
        self.input_tokens += response['usage']['prompt_tokens']
        self.output_tokens += response['usage']['completion_tokens']
        #print('prompt: \n\n',content)
        #print('response: \n',response['choices'][0]['message']['content'])
        #print('='*60)
        #assert False
        return response['choices'][0]['message']['content']

    def _init_chat(self,model):
        if model == 'chatgpt':
            return self.gpt_chat
        elif model == 'llama':
            return self.llama_chat
        elif model == 'gemini':
            return self.gemini_chat
        elif model == 'deepseek':
            return self.deepseek_chat

    def _init_model(self,model):
        if model == 'chatgpt':
            return self._init_chatgpt()
        elif model == 'llama':
            return self._init_llama()
        elif model == 'gemini':
            return self._init_gemini()
        elif model == 'deepseek':
            return self._init_deepseek()

    def _init_deepseek(self):
        client = OpenAI(api_key="", base_url="https://api.deepseek.com")
        return client
    
    def deepseek_chat(self,content):
        response = self.model.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful chemist and biologist"},
                {"role": "user", "content": content},
            ],
            stream=False
        )
        return response.choices[0].message.content
    
    def _init_gemini(self):
        genai.configure(api_key="")
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    
    def gemini_chat(self,content):
        response = self.model.generate_content(content)
        print(response.text)
        return response.text

    def _init_llama(self):
        client = OpenAI(
            base_url="http://localhost:8000/v1",
            api_key="token-abc123",
        )
        return client
    
    def llama_chat(self,content):
        completion = self.model.chat.completions.create(
            model="NousResearch/Meta-Llama-3-8B-Instruct",
            messages=[
                {"role": "user", "content": content}
            ]
        )
        return completion.choices[0].message.content
        


    def _init_chatgpt(self):
        # Set the necessary variables
        resource_name = "ds-chatgpt4o-ai-swedencentral"#"gcrgpt4aoai2c" sfm-openai-sweden-central  ds-chatgpt4o-ai-swedencentral
        endpoint = f"https://{resource_name}.openai.azure.com/"
        api_version = "2024-02-15-preview"  # Replace with the appropriate API version

        azure_credential = ChainedTokenCredential(
            AzureCliCredential(),
            DefaultAzureCredential(
                exclude_cli_credential=True,
                # Exclude other credentials we are not interested in.
                exclude_environment_credential=True,
                exclude_shared_token_cache_credential=True,
                exclude_developer_cli_credential=True,
                exclude_powershell_credential=True,
                exclude_interactive_browser_credential=True,
                exclude_visual_studio_code_credentials=True,
                managed_identity_client_id=os.environ.get("DEFAULT_IDENTITY_CLIENT_ID"),
            )
        )

        token_provider = get_bearer_token_provider(azure_credential,
            "https://cognitiveservices.azure.com/.default")
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider
        )
        
        
        return client
    
    def gpt_chat(self, content):
        completion = self.model.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who can propose novel and powerful molecules based on your domain knowledge."},
                {
                    "role": "user",
                    "content": content,
                },
            ],
        )
        res = completion.choices[0].message.content
        return res