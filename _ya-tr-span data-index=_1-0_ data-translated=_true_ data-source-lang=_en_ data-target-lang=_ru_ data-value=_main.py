pip install celery


Шаг 3: Конфигурация Django
- Создайте новый проект Django с помощью команды:

django-admin startproject project_name

- Установите необходимые пакеты для Django:

pip install django-redis django-celery-results

- В settings.py вашего проекта, добавьте следующие строки:
python
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

- Также, добавьте следующие строки в конец вашего settings.py:
python
import djcelery
djcelery.setup_loader()


Шаг 4: Реализация рассылки уведомлений
- В вашем приложении Django, создайте файл tasks.py и добавьте следующий код:
python
from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail

@shared_task
def send_notification_email(subject, message, recipient_list):
    send_mail(subject, message, 'from@example.com', recipient_list)

- Вам также понадобится создать модель для новости и добавить в нее сигнал, который будет вызываться при создании новости и отправлять уведомления подписчикам. Например:
python
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class News(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

@receiver(post_save, sender=News)
def send_news_notification(sender, instance, **kwargs):
    subscribers = User.objects.filter(subscribe=True)
    recipient_list = [subscriber.email for subscriber in subscribers]
    subject = 'New News Alert!'
    message = 'A new news has been created: {}'.format(instance.title)
    send_notification_email.delay(subject, message, recipient_list)


Шаг 5: Реализация еженедельной рассылки
- В файле tasks.py вашего приложения Django добавьте следующий код:
python
from datetime import datetime, timedelta
from celery.schedules import crontab
from celery.task import periodic_task
from .models import News

@periodic_task(run_every=crontab(day_of_week='mon', hour=8))
def send_weekly_newsletter():
    last_week = datetime.now() - timedelta(days=7)
    latest_news = News.objects.filter(created_at__gte=last_week)
    subscribers = User.objects.filter(subscribe=True)
    recipient_list = [subscriber.email for subscriber in subscribers]
    subject = 'Weekly News Digest'
    message = 'Here are the latest news from the past week:\n\n{}'.format(
        '\n'.join(news.title for news in latest_news)
    )
    send_notification_email.delay(subject, message, recipient_list)


Шаг 6: Запуск Celery
- Запустите Celery командой:

celery -A project_name worker -l info