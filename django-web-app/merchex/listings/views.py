from django.http import HttpResponse

from django.shortcuts import render


def hello(request):
    
    return HttpResponse('<h1>Hello Django!</h1>')

def about(request):
    return HttpResponse('<h1>À propos de nous</h1> <p>Nous adorons merch !</p>')

def list(request) :
    return HttpResponse('<h1>Liste de commande</h1> <p>Pas à Pas !</p>')

def contact(request):
    return HttpResponse('<h1>Contact us</h1> <p>Tous les contact !</p>')