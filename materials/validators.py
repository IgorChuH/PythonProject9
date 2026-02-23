from rest_framework.serializers import ValidationError

def validate_youtube_link(value):
    """Проверяет, что ссылка ведёт на YouTube."""
    allowed_domains = ['youtube.com', 'youtu.be']
    # Проверяем наличие домена в ссылке (простая проверка)
    if not any(domain in value for domain in allowed_domains):
        raise ValidationError('Ссылка должна быть только на YouTube (youtube.com или youtu.be)')
    return value