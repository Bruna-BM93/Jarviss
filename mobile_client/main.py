import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

API_URL = 'http://localhost:5000'

class LoginScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text='Usuário'))
        self.username = TextInput(multiline=False)
        self.add_widget(self.username)
        self.add_widget(Label(text='Senha'))
        self.password = TextInput(password=True, multiline=False)
        self.add_widget(self.password)
        btn = Button(text='Login')
        btn.bind(on_press=self.do_login)
        self.add_widget(btn)
        self.msg = Label(text='')
        self.add_widget(self.msg)

    def do_login(self, instance):
        data = {
            'usuario': self.username.text,
            'senha': self.password.text,
        }
        try:
            r = requests.post(f'{API_URL}/login', json=data)
            res = r.json()
            self.msg.text = res.get('mensagem', res.get('erro', 'Erro'))
        except Exception as e:
            self.msg.text = str(e)

class JarvissApp(App):
    def build(self):
        return LoginScreen()

if __name__ == '__main__':
    JarvissApp().run()
