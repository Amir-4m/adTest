from rest_framework import throttling


class SendEmailThrottle(throttling.AnonRateThrottle):
    scope = 'send-email'


class LoginThrottle(throttling.AnonRateThrottle):
    scope = 'login'
