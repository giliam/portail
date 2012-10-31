# -*- coding: utf-8 -*-
from django.db import models
from trombi.models import UserProfile
from django.db.models import Q
from django.contrib.auth.models import Permission, User
from notification.models import Notification

class Sondage(models.Model):
    auteur = models.ForeignKey(UserProfile)
    question = models.CharField(max_length=512)
    reponse1 = models.CharField(max_length=200)
    reponse2 = models.CharField(max_length=200)
    deja_paru = models.BooleanField()    
    date_parution = models.DateField(null=True, blank=True)
    autorise = models.BooleanField()
    resultat = models.IntegerField(editable=False)
    
    def date_str(self):
        jour = str(self.date_parution.day)
        mois = str(self.date_parution.month)
        if self.date_parution.day < 10:
            jour = '0' + jour
        if self.date_parution.month < 10:
            mois = '0' + mois
        return jour + '/' + mois + '/' + str(self.date_parution.year)
    
    def __unicode__(self):
        return self.question
        
    def calculer_resultat(self):
        from django.db.models import Count
        votes = Vote.objects.filter(sondage = self)
        if votes:
            return votes.values('choix').annotate(c=Count('choix')).order_by('-c')[0]['choix']
        else:
            return 0
        # nombre_votes_1 = votes.filter(choix = 1).count()
        # nombre_votes_2 = votes.filter(choix = 2).count()
        # if (nombre_votes_2 > nombre_votes_1) :
            # return 2
        # else:
            # return 1
        
    def envoyer_notification(self):
        try: 
            perm = Permission.objects.get(codename='add_sondage')  #On envoie seulement à ceux qui peuvent créer des sondages
            users = User.objects.filter(Q(is_superuser=True) | Q(groups__permissions=perm) | Q(user_permissions=perm) ).distinct()            
            notification = Notification(content_object=self, message='Un nouveau sondage a été proposé')
            notification.save()
            notification.envoyer_multiple(users)
        except Permission.DoesNotExist:
            pass

    def save(self, *args, **kwargs):
        self.resultat = self.calculer_resultat()
        super(Sondage, self).save(*args, **kwargs)


        
class Vote(models.Model):
    sondage = models.ForeignKey(Sondage)
    eleve = models.ForeignKey(UserProfile)
    choix = models.IntegerField()
    
    def __unicode__(self):
        return self.eleve.user.username + ' -> ' + self.sondage.question