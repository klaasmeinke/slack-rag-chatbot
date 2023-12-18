from smartsearch.chat_interfaces.interface import Interface


class CliInterface(Interface):
    def __call__(self):
        while True:
            prompt = input('Prompt: ')
            if prompt.lower().strip() == 'exit':
                break

            print(f'Response: ', end='')
            response = self.get_response(prompt=prompt, user_id='1')
            print(response)
