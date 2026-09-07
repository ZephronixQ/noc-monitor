from django.db import models
from django.utils import timezone


class Cluster(models.Model):
    name = models.CharField("Название локации", max_length=150, unique=True)
    order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        verbose_name = "Локация / Папка"
        verbose_name_plural = "Локации / Папки"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Switch(models.Model):
    ip = models.GenericIPAddressField("IP адрес", unique=True)
    description = models.CharField("Адрес / Описание", max_length=255)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name='switches', verbose_name="Локация")
    is_active = models.BooleanField("Опрашивать", default=True)
    model_override = models.CharField("Модель (если не определена по SNMP)", max_length=100, blank=True)

    class Meta:
        verbose_name = "Коммутатор"
        verbose_name_plural = "Коммутаторы"
        ordering = ['cluster', 'ip']

    def __str__(self):
        return f"{self.ip} — {self.description}"


class OltDevice(models.Model):
    MODEL_CHOICES = [
        ('c300', 'ZTE C300 / C320'),
        ('c600', 'ZTE C600 / C650'),
    ]

    ip = models.GenericIPAddressField("IP адрес", unique=True)
    model_type = models.CharField("Тип станции", max_length=20, choices=MODEL_CHOICES, default='c300')
    username = models.CharField("Логин Telnet", max_length=50, default="admin")
    password = models.CharField("Пароль Telnet", max_length=100)
    port = models.PositiveIntegerField("Порт", default=23)
    is_active = models.BooleanField("Опрашивать", default=True)

    class Meta:
        verbose_name = "OLT станция"
        verbose_name_plural = "OLT станции"
        ordering = ['ip']

    def __str__(self):
        return f"OLT {self.ip} ({self.get_model_type_display()})"


class Incident(models.Model):
    TYPE_CHOICES = [
        ('sw', 'Коммутатор L2'),
        ('olt', 'OLT Станция'),
        ('onu', 'Оптика GPON ONU'),
    ]

    target_id = models.CharField("Идентификатор узла (IP или OLT:Port:ONU)", max_length=100, db_index=True)
    device_type = models.CharField("Тип устройства", max_length=10, choices=TYPE_CHOICES, default='sw')
    contract = models.CharField("Договор / Описание", max_length=255, default="—", blank=True)
    start_time = models.IntegerField("Время старта (UNIX)", db_index=True)
    end_time = models.IntegerField("Время восстановления (UNIX)", null=True, blank=True, db_index=True)
    duration = models.IntegerField("Длительность (сек)", default=0)

    class Meta:
        verbose_name = "Инцидент"
        verbose_name_plural = "История инцидентов"
        ordering = ['-start_time']

    @property
    def is_active(self):
        return self.end_time is None

    def close(self, end_ts=None):
        now = end_ts or int(timezone.now().timestamp())
        self.end_time = now
        self.duration = max(0, now - self.start_time)
        self.save()