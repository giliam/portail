﻿# -*- coding: utf-8 -*-
from messages.models import Message
from trombi.models import UserProfile
from messages.models import MessageForm
from association.models import Association, Adhesion
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.utils import simplejson
from django.template import RequestContext
from django.db.models import Q
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from messages.utils import sanitizeHtml
from django.views.decorators.http import require_POST
from django.contrib import comments
from django.db import models
from django.contrib.comments import signals
from django.contrib import messages
import settings





#La liste des nouveaux messages
def index(request):
    #On sélectionne les messages publics, et les messages dont l'utilisateur fait partie de l'assoce expeditrice, ou de l'assoce destinataires.
    if not request.user.is_authenticated():
        return render_to_response('accueil/accueil.html', {},context_instance=RequestContext(request))
    else:
        eleve = request.user.get_profile()
        list_messages = Message.accessibles_par(eleve).exclude(lu=eleve)
        paginator = Paginator(list_messages, 15)
        page = request.GET.get('page')
        try:
            list_messages = paginator.page(page)
        except PageNotAnInteger:
            list_messages = paginator.page(1)
        except EmptyPage:
            list_messages = paginator.page(paginator.num_pages)
        return render_to_response('messages/index.html', {'list_messages': list_messages},context_instance=RequestContext(request))

@login_required
#La liste des nouveaux messages, sérialisée aux format JSON (pour les applis)
def index_json(request):
    eleve = request.user.get_profile()
    list_messages = Message.accessibles_par(eleve).exclude(lu=eleve)
    response = HttpResponse(mimetype='application/json')
    response.write(simplejson.dumps([{
            'id': m.id,
            'association': m.association.nom,
            'association_pseudo': m.association.pseudo,
            'objet': m.objet,
            'contenu': m.html_to_text(),
            'date': str(m.date.day)+'/'+str(m.date.month)+'/'+str(m.date.year)+ " " + str(m.date.hour) + ":" + str(m.date.minute),
            'expediteur': m.expediteur.user.username,
            'important': request.user.get_profile() in m.important.all()
        } for m in list_messages]))
    return response
    
@login_required
#L'affichage des détails d'un message (de ses commentaires)
def detail(request, message_id):
    m = get_object_or_404(Message, pk=message_id)
    return render_to_response('messages/detail.html', {'message': m},context_instance=RequestContext(request))
    
@login_required
#Permet de classer un message comme lu (UNSAFE via un GET --> A changer en POST)
def lire(request, message_id):
    m = get_object_or_404(Message, pk=message_id)    
    m.lu.add(request.user.get_profile())
    m.save()
    
    return render_to_response('messages/action.html', {'message': m},context_instance=RequestContext(request))
    
@login_required
#Permet de classer un message comme important (UNSAFE via un GET --> A changer en POST)
def classer_important(request, message_id):
    m = get_object_or_404(Message, pk=message_id)
    m.important.add(request.user.get_profile())
    m.lu.add(request.user.get_profile())
    m.save()
    
    return render_to_response('messages/action.html', {'message': m},context_instance=RequestContext(request))

@login_required    
#Permet de classer un message comme non important (UNSAFE via un GET --> A changer en POST)
def classer_non_important(request, message_id):
    m = get_object_or_404(Message, pk=message_id)
    m.important.remove(request.user.get_profile())    
    m.save()
    
    return render_to_response('messages/action.html', {'message': m},context_instance=RequestContext(request))

@login_required
#Permet de classer un message comme non lu (UNSAFE via un GET --> A changer en POST)
def classer_non_lu(request, message_id):
    m = get_object_or_404(Message, pk=message_id)
    m.lu.remove(request.user.get_profile())
    m.save()
    
    return render_to_response('messages/action.html', {'message': m},context_instance=RequestContext(request))
    
@login_required
#La liste des messages, y compris les messages lus
def tous(request):
    all_messages = Message.accessibles_par(request.user.get_profile())
    
    paginator = Paginator(all_messages, 15)
    page = request.GET.get('page')
    try:
        list_messages = paginator.page(page)
    except PageNotAnInteger:        
        list_messages = paginator.page(1)
    except EmptyPage:        
        list_messages = paginator.page(paginator.num_pages)
    
    return render_to_response('messages/tous.html', {'list_messages': list_messages},context_instance=RequestContext(request))


@login_required
def tous_json(request):
    all_messages = Message.accessibles_par(request.user.get_profile())
    response = HttpResponse(mimetype='application/json')
    response.write(simplejson.dumps([{
            'id': m.id,
            'association': m.association.nom,
            'association_pseudo': m.association.pseudo,
            'objet': m.objet,
            'contenu': m.html_to_text(),
            'date': str(m.date.day)+'/'+str(m.date.month)+'/'+str(m.date.year)+ " " + str(m.date.hour) + ":" + str(m.date.minute), 
            'expediteur': m.expediteur.user.username,
            'lu': request.user.get_profile() in m.lu.all(),
            'important': request.user.get_profile() in m.important.all()           
        } for m in all_messages]))
    return response
    
    
@login_required
#La liste des messages classés importants
def importants(request):
    eleve = request.user.get_profile()
    list_messages = Message.accessibles_par(eleve).filter(important=eleve)
    return render_to_response('messages/importants.html', {'list_messages': list_messages},context_instance=RequestContext(request))
    

@login_required
#La création d'un nouveau message par une association
def nouveau(request, association_pseudo):
    if request.method == 'POST':
        eleve = request.user.get_profile()
        association = get_object_or_404(Association,pseudo=association_pseudo)    
        if Adhesion.existe(eleve, association):
            #On cree le message SANS OUBLIER de passer par le SANITIZER, pour escaper le js et les tags html non autorisés
            message = Message.objects.create(expediteur=eleve,association=association,objet=sanitizeHtml(request.POST['objet']),contenu=sanitizeHtml(request.POST['contenu']),date=datetime.now())
        return redirect(message)
    else:
        liste_assoces = Association.objects.all()
        form = MessageForm()
        return render_to_response('messages/nouveau.html', {'liste_assoces': liste_assoces, 'form':form},context_instance=RequestContext(request))
        
@login_required
def supprimer(request, message_id):
    message = get_object_or_404(Message, pk = message_id)
    association = message.association
    if Adhesion.existe(request.user.get_profile(), association):
        message.delete()
        messages.add_message(request, messages.SUCCESS, "Message supprimé !")
    return redirect(association.get_absolute_url() + 'messages/')

        

@require_POST
def post_comment(request, next=None, using=None):
    """
    Post a comment.

    HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``comments/preview.html``, will be rendered.
    """
    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    if request.user.is_authenticated():
        if not data.get('name', ''):
            data["name"] = request.user.get_full_name() or request.user.username
        if not data.get('email', ''):
            data["email"] = request.user.email

    # Check to see if the POST data overrides the view's next argument.
    next = data.get("next", next)

    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")
    model = models.get_model(*ctype.split(".", 1))
    target = model._default_manager.using(using).get(pk=object_pk)


    # Construct the comment form
    form = comments.get_form()(target, data=data)

    # Check security information
    if form.security_errors():
        return None
    # Create the comment
    comment = form.get_comment_object()
    comment.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated():
        comment.user = request.user

    # Signal that the comment is about to be saved
    responses = signals.comment_will_be_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )

    # Save the comment and signal that it was saved
    comment.save()
    message = get_object_or_404(Message, pk = object_pk)
    message.envoyer_commentaire_notification(comment.pk, request.user.username)
    
    signals.comment_was_posted.send(
        sender  = comment.__class__,
        comment = comment,
        request = request
    )

    comment_list = [comment]
    return render_to_response('comments/list.html', {'comment_list': comment_list},context_instance=RequestContext(request))
    
@login_required
@require_POST
def delete_own_comment(request):
    comment = get_object_or_404(comments.get_model(), pk=int(request.POST['comment_id']),
            site__pk=settings.SITE_ID)
    response = HttpResponse(mimetype='text/html')
    if comment.user == request.user:
        comment.delete()
        response.write('deleted')
    return response
    

@login_required
def edit(request, message_id=None):
    if message_id:
        message = get_object_or_404(Message, pk=message_id)
        if message.expediteur != request.user.get_profile():
            return HttpResponseForbidden()
    else:
        return HttpResponseForbidden()

    if request.POST:
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            message = form.save()
            message.objet=sanitizeHtml(message.objet)
            message.contenu=sanitizeHtml(request.POST['contenu'])
            message.save()

            # If the save was successful, redirect to another page
            redirect_url = message.get_absolute_url()#reverse(article_save_success)
            return HttpResponseRedirect(redirect_url)

    else:
        form = MessageForm(instance=message)

    return render_to_response("messages/nouveau.html", {
        'form': form,
    }, context_instance=RequestContext(request))