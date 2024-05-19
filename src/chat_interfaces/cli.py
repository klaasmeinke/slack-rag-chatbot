from src.chat_interfaces.type import ChatInterface


class CliInterface(ChatInterface):
    def __call__(self):
        while True:
            prompt = input('Prompt: ')
            if prompt.lower().strip() == 'exit':
                break

            print(f'Response: ', end='')
            response = self.get_response(prompt=prompt, user_id='1')
            print(response)
