from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import BuyerProfile, ProducerProfile, TransporterProfile
from products.models import Product
from orders.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = "Charge des données de démonstration réalistes pour AgriConnect."

    def handle(self, *args, **options):
        self.stdout.write("Création des données de démonstration...")
        admin = self._create_user(
            username="admin",
            email="admin@agriconnect.tg",
            password="Admin12345!",
            first_name="Kofi",
            last_name="Admin",
            role=User.Roles.ADMIN,
            city="Lomé",
            phone="+228 90 00 00 01",
            is_staff=True,
            is_superuser=True,
        )

        p1 = self._create_user("ama_prod", "ama@agriconnect.tg", "Demo12345!", "Ama", "Kossi", User.Roles.PRODUCTEUR, "Kpalimé", "+228 90 11 11 11")
        p2 = self._create_user("yaw_prod", "yaw@agriconnect.tg", "Demo12345!", "Yaw", "Mensah", User.Roles.PRODUCTEUR, "Atakpamé", "+228 90 22 22 22")
        ProducerProfile.objects.update_or_create(user=p1, defaults={"farm_name": "Ferme Ama Verde", "description": "Production de légumes frais et fruits locaux."})
        ProducerProfile.objects.update_or_create(user=p2, defaults={"farm_name": "Coopérative Yaw", "description": "Céréales et tubercules de qualité pour grossistes."})

        b1 = self._create_user("akua_buy", "akua@agriconnect.tg", "Demo12345!", "Akua", "Adjo", User.Roles.ACHETEUR, "Lomé", "+228 90 33 33 33")
        b2 = self._create_user("kodjo_buy", "kodjo@agriconnect.tg", "Demo12345!", "Kodjo", "Tetteh", User.Roles.ACHETEUR, "Sokodé", "+228 90 44 44 44")
        BuyerProfile.objects.update_or_create(user=b1, defaults={"company_name": "Marché Central Lomé", "business_type": "Commerce de détail"})
        BuyerProfile.objects.update_or_create(user=b2, defaults={"company_name": "RestoFresh", "business_type": "Restauration"})

        t1 = self._create_user("femi_trans", "femi@agriconnect.tg", "Demo12345!", "Femi", "Lawson", User.Roles.TRANSPORTEUR, "Lomé", "+228 90 55 55 55")
        TransporterProfile.objects.update_or_create(user=t1, defaults={"company_name": "Femi Logistics", "vehicle_type": "Camionnette", "coverage_area": "Lomé, Kpalimé, Atakpamé", "capacity": "2 tonnes"})

        products_data = [
            (p1, "Tomates fraîches", Product.Category.LEGUMES, "Tomates rouges récoltées du jour, idéales pour revendeurs et restaurants.", Decimal("850"), Product.Unit.KG, 120, "Kpalimé"),
            (p1, "Piments verts", Product.Category.LEGUMES, "Piments locaux bien frais, sachets ou vrac.", Decimal("1200"), Product.Unit.KG, 60, "Kpalimé"),
            (p1, "Ananas sucrés", Product.Category.FRUITS, "Ananas mûrs et sucrés, calibre moyen.", Decimal("700"), Product.Unit.PIECE, 200, "Kpalimé"),
            (p2, "Maïs blanc", Product.Category.CEREALES, "Maïs sec de bonne qualité, bien trié.", Decimal("18000"), Product.Unit.SAC, 45, "Atakpamé"),
            (p2, "Igname", Product.Category.TUBERCULES, "Ignames fraîches, grosses pièces.", Decimal("25000"), Product.Unit.SAC, 30, "Atakpamé"),
            (p2, "Soja", Product.Category.LEGUMINEUSES, "Soja propre et sec, prêt pour transformation.", Decimal("22000"), Product.Unit.SAC, 25, "Atakpamé"),
        ]

        products = []
        for producer, name, cat, desc, price, unit, qty, loc in products_data:
            obj, _ = Product.objects.update_or_create(
                producer=producer,
                name=name,
                defaults={
                    "category": cat,
                    "description": desc,
                    "price": price,
                    "unit": unit,
                    "quantity": qty,
                    "location": loc,
                    "is_available": True,
                },
            )
            products.append(obj)

        # Create sample orders if none exist
        if not Order.objects.exists():
            o1 = Order.objects.create(
                buyer=b1, product=products[0], producer=products[0].producer,
                quantity=20, unit_price=products[0].price, total_price=products[0].price * 20,
                status=Order.Status.EN_ATTENTE, delivery_address="Marché Central, Lomé", note="Livraison tôt le matin."
            )
            o2 = Order.objects.create(
                buyer=b2, product=products[3], producer=products[3].producer,
                quantity=2, unit_price=products[3].price, total_price=products[3].price * 2,
                status=Order.Status.CONFIRMEE, delivery_address="RestoFresh, Sokodé", transporter=t1
            )
            o3 = Order.objects.create(
                buyer=b1, product=products[4], producer=products[4].producer,
                quantity=1, unit_price=products[4].price, total_price=products[4].price * 1,
                status=Order.Status.EN_LIVRAISON, delivery_address="Entrepôt Lomé", transporter=t1
            )
            # adjust stock for seeded orders
            for o in [o1, o2, o3]:
                p = o.product
                p.quantity = max(0, p.quantity - o.quantity)
                if p.quantity == 0:
                    p.is_available = False
                p.save(update_fields=["quantity", "is_available", "updated_at"])

        self.stdout.write(self.style.SUCCESS("Données de démonstration créées."))
        self.stdout.write("Comptes: admin/Admin12345!, ama_prod/Demo12345!, yaw_prod/Demo12345!, akua_buy/Demo12345!, kodjo_buy/Demo12345!, femi_trans/Demo12345!")

    def _create_user(self, username, email, password, first_name, last_name, role, city, phone, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "city": city,
                "phone": phone,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        else:
            # ensure role/flags for demo consistency
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.city = city
            user.phone = phone
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(password)
            user.save()
        return user
