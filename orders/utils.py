# orders/utils.py
from .models import TrackingLog

def update_order_status(order, new_status, note=None):
    order.status = new_status
    order.save()
    TrackingLog.objects.create(order=order, status=new_status, note=note)
