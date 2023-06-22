from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat
from django.utils import timezone
from py2neo import Graph
from django.urls import reverse
import aiml,os
import openai
import pytholog as pl
from dotenv import load_dotenv


#learning aiml

k = aiml.Kernel()
k.learn("aiml/*.aiml")

#you can also use the brain method

# if os.path.isfile("brain_bot/brain.brn"):
#     k.bootstrap(brainFile="brain_bot/brain.brn")
# else:
#     k.bootstrap(learnFiles="aiml/*.aiml",commands="load aiml b")
#     k.saveBrain("brain_bot/brain.brn")

#---------------------------------------------------------------------

# Set up OpenAI API
load_dotenv()
openai.api_key = os.getenv("SECRET_API_KEY")
graph = Graph("bolt://localhost:7687", auth=("neo4j", "12345678"))
# graph.run("create (bot:ATOM {name:$name})",name="ATOM")

#pytholog integration
kb = pl.KnowledgeBase("parent")

def generate_image_creatives(message):
    response = openai.Completion.create(
        engine="davinci",
        prompt=message,
        max_tokens=200,
        temperature=0.7,
        n=1,
        stop=None
    )

    creative = response.choices[0].text.strip()
    return creative

def ask_openai(message):
    msg = openai.Completion.create(engine="text-davinci-003",prompt=message,max_tokens=50,temperature=0.7,n=1,stop = None)

    return msg.choices[0].text.strip()

def chatbot(request):
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user)

        if request.method == 'POST':
            message = request.POST.get('message')

            if any(salutation in message.lower() for salutation in ["hi", "hello", "hey"]):
                response = "Hi! I am A.T.O.M. Nice to meet you. How can I assist you today?"
            elif any(salutation in message.lower() for salutation in ["salam", "assalam o alikum", "aoa"]) or any(
                    salutation in message.upper() for salutation in ["SALAM", "ASSALAM O ALIKUM", "AOA"]):
                response = "Walikum Salam! I am A.T.O.M. Nice to meet you. How can I assist you today?"
            elif any(keyword in message.lower() for keyword in
                    ["creator", "made", "who created you", "who made you", "who created you?", "who made u?"]):
                response = "I was created by Usman Ghani. He is a really talented developer."
            else:
                response = k.respond(message)
                Father = k.getPredicate("father")
                Username = request.user
                if "try" in response or "Try" in response:
                    response = ask_openai(message)
                if Father:
                   kb(["isFatherof(Father,request.user)"])
                   kb.query(pl.Expr(f"isFatherof({Father},{Username})"))
                   fathId = graph.evaluate("create (p:Person {name:$name}) return id(p)",name=Father)
                   userId = graph.evaluate(f"match (u:User) where u.username = '{Username}' return id(u)")
                   graph.run(f"match (p:Person),(u:User) where id(u) = {userId} and id(p) = {fathId} "
                             "create (p)-[:isFatherof]->(u)")

            chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
            chat.save()

            return JsonResponse({'message': message, 'response': response})

        return render(request, 'main.html',{"chats":chats})
    else:
        return redirect('/login')

# Rest of the code (login, register, logout views, HTML templates, etc.) remains unchanged.



def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        register_url = reverse('register')  # Get the URL for the register page
        return render(request, 'login.html', {'register_url': register_url})


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            user = User.objects.create_user(username, email, password1)
            user.save()
            auth.login(request, user)

            # Create the dataToGet dictionary with user data
            dataToGet = {
                'username': username,
                'email': email,
                'password1': password1,
                'password2': password2
            }
            userId = graph.evaluate("CREATE (p:Person:User {username: $username, email: $email, password1: $password1, password2: $password2}) return id(p)", **dataToGet)
            graph.run(f"match (p:User),(a:ATOM) where id(p) = {userId} and id(a) = 7 merge (a)-[:KNOWS]->(p) ")

            return redirect('chatbot')
        else:
            error_message = "Passwords don't match"
            return render(request, 'register.html', {'error_message': error_message})
    else:
        login_url = reverse('login')  # Get the URL for the login page
        return render(request, 'register.html', {'login_url': login_url})


def logout(request):
    auth.logout(request)
    return redirect('login')
