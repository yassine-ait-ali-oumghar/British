from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from apps.core.models import Employee, Service, Product, Reservation, Order, OrderItem, Payment
import datetime

class ReceptionPaymentsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create receptionist user
        self.receptionist_user = User.objects.create_user(
            username='receptionist1',
            email='reception@salon.ma',
            password='Password123!',
            first_name='Salma',
            last_name='Ben'
        )
        self.receptionist_user.employee_profile.role = 'RECEPTION'
        self.receptionist_user.employee_profile.save()

        # Create client user
        self.client_user = User.objects.create_user(
            username='sarah_client',
            email='sarah@example.com',
            password='Password123!',
            first_name='Sarah',
            last_name='Alami'
        )

        # Create employee (coiffeuse)
        self.stylist_user = User.objects.create_user(
            username='emma_stylist',
            password='Password123!',
            first_name='Emma',
            last_name='Rocher'
        )
        self.stylist_emp = self.stylist_user.employee_profile
        self.stylist_emp.role = 'EMPLOYEE'
        self.stylist_emp.is_team_member = True
        self.stylist_emp.save()

        # Create service
        self.service_coloration = Service.objects.create(
            name="Coloration Prestige",
            category="Coiffure",
            price=250.00,
            duration_minutes=60
        )

        # Create appointment (Reservation)
        today = timezone.localtime(timezone.now()).date()
        self.reservation = Reservation.objects.create(
            client=self.client_user,
            employee=self.stylist_emp,
            service=self.service_coloration,
            date=today,
            start_time=datetime.time(14, 0),
            end_time=datetime.time(15, 0),
            status='COMPLETED'
        )

        # Create Click & Collect Order
        self.order_click_collect = Order.objects.create(
            client=self.client_user,
            client_name="Sarah Alami",
            client_phone="0600000000",
            subtotal=150.00,
            total=150.00,
            delivery_mode='CLICK_COLLECT',
            payment_mode='STORE',
            order_status='READY_FOR_PICKUP',
            payment_status='PENDING'
        )

        # Create Home Delivery Order (COD)
        self.order_delivery = Order.objects.create(
            client=self.client_user,
            client_name="Sarah Alami",
            client_phone="0600000000",
            subtotal=200.00,
            total=200.00,
            delivery_mode='DELIVERY',
            payment_mode='COD',
            order_status='DELIVERING',
            payment_status='PENDING'
        )

    def test_pay_reservation_updates_caisse_and_prevents_duplicate(self):
        """Test paying a reservation links payment, logs receptionist, and prevents duplicate."""
        self.client.login(username='receptionist1', password='Password123!')

        self.assertFalse(self.reservation.is_paid)

        # Pay reservation
        response = self.client.post('/reception/payments/', {
            'action': 'pay_reservation',
            'reservation_id': self.reservation.id,
            'amount': '250.00',
            'payment_method': 'CARD',
            'notes': 'Paiement carte bancaire'
        })
        self.assertEqual(response.status_code, 302)

        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.is_paid)

        # Verify Payment model instance created
        payment = Payment.objects.get(reservation=self.reservation)
        self.assertEqual(payment.amount, 250.00)
        self.assertEqual(payment.payment_method, 'CARD')
        self.assertEqual(payment.receptionist, self.receptionist_user)
        self.assertEqual(payment.origin_info['code'], 'SERVICE')

        # Try duplicate payment
        response_dup = self.client.post('/reception/payments/', {
            'action': 'pay_reservation',
            'reservation_id': self.reservation.id,
            'amount': '250.00',
            'payment_method': 'CASH'
        })
        self.assertEqual(response_dup.status_code, 302)
        # Should still have only 1 payment for this reservation
        self.assertEqual(Payment.objects.filter(reservation=self.reservation).count(), 1)

    def test_pay_order_click_collect(self):
        """Test paying click & collect order marks it PAID and RETRIEVED."""
        self.client.login(username='receptionist1', password='Password123!')

        response = self.client.post('/reception/payments/', {
            'action': 'pay_order',
            'order_id': self.order_click_collect.id,
            'amount': '150.00',
            'payment_method': 'CASH',
            'mark_retrieved': 'true'
        })
        self.assertEqual(response.status_code, 302)

        self.order_click_collect.refresh_from_db()
        self.assertEqual(self.order_click_collect.payment_status, 'PAID')
        self.assertEqual(self.order_click_collect.order_status, 'RETRIEVED')

        payment = Payment.objects.get(order=self.order_click_collect)
        self.assertEqual(payment.amount, 150.00)
        self.assertEqual(payment.origin_info['code'], 'CLICK_COLLECT')

    def test_refund_deducts_from_caisse(self):
        """Test processing refund changes status to REFUNDED and records reason & user."""
        self.client.login(username='receptionist1', password='Password123!')

        # Create a paid payment first
        payment = Payment.objects.create(
            client=self.client_user,
            amount=100.00,
            payment_method='CASH',
            status='PAID',
            receptionist=self.receptionist_user
        )

        response = self.client.post('/reception/payments/', {
            'action': 'refund',
            'payment_id': payment.id,
            'refund_reason': 'Satisfaction client'
        })
        self.assertEqual(response.status_code, 302)

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'REFUNDED')
        self.assertEqual(payment.refund_reason, 'Satisfaction client')
        self.assertEqual(payment.refunded_by, self.receptionist_user)
        self.assertIsNotNone(payment.refunded_at)
