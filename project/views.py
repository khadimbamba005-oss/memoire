from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login


def connexion(request):
    return render(request , 'login.html')


def connexion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print("username:" , username)
        print("Password:", password)


        user = authenticate(request,username=username ,password = password)

        if user is not None:
            print("Connexion reussi")
            login(request,user)
            return redirect('dashoboard_admin')
        else:
            print("Echec de la connexion")
            return render(request , 'login.html',{
                'error':'Indentifiants incorrects'
            })
    return render(request , 'login.html')