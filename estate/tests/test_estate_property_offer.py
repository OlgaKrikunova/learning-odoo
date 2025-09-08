from datetime import timedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class EstatePropertyOfferTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_partner = cls.env["res.partner"].create(
            {  # создание тестового партнера
                "name": "Test Buyer",
                "email": "buyer@test.com",
            }
        )

        # Создаем недвижимость для оффера
        cls.test_property = cls.env["estate.property"].create(
            {
                "name": "Test Villa",
                "expected_price": 100001,
                "living_area": 120,
                "state": "new",
            }
        )

        offer_validity = 7
        base_date = fields.Date.today()

        # Создаем несколько тестовых офферов
        cls.offer = cls.env["estate.property.offer"].create(
            [
                {
                    "price": 100000,
                    "partner_id": cls.test_partner.id,
                    "validity": offer_validity,
                    "date_deadline": base_date + timedelta(days=offer_validity),
                    "status": "refused",
                    "property_id": cls.test_property.id,
                },
                {
                    "price": 15000,
                    "partner_id": cls.test_partner.id,
                    "validity": 10,
                    "date_deadline": base_date + timedelta(days=offer_validity),
                    "status": "refused",
                    "property_id": cls.test_property.id,
                },
            ]
        )

    def test_01_compute_date_deadline(self):
        """вычисление даты дедлайна"""
        expected_date = fields.Date.today() + timedelta(days=self.offer[0].validity)
        self.assertEqual(
            self.offer[0].date_deadline,
            expected_date,
            "Date deadline should be sum of base_date + timedelta(days=offer.validity)",
        )

    def test_02_inverse_date_deadline(self):
        """обратная дата дедлайна"""
        base_date = fields.Date.today()
        delta = self.offer[0].date_deadline - base_date  # это timedelta

        self.assertEqual(
            delta,
            timedelta(days=self.offer[1].validity),
            "Date deadline should be subtraction of offer.date_deadline - base_date",
        )

    def test_03_action_accept_offer(self):
        """Тест: принятие оффера"""

        offer_to_accept = self.offer[0]  # выбираем оффер для принятия
        other_offer = self.offer[1]  # другой оффер на ту же недвижимость

        # Вызов метода
        offer_to_accept.action_accept()

        # Проверка, что текущий оффер принят
        self.assertEqual(offer_to_accept.status, "accepted")

        # Проверка, что все другие офферы отклонены
        self.assertEqual(other_offer.status, "refused")

        # Проверка, что недвижимость обновилась
        property = offer_to_accept.property_id
        self.assertEqual(property.buyer_id.id, offer_to_accept.partner_id.id)
        self.assertEqual(property.selling_price, offer_to_accept.price)
        self.assertEqual(property.state, "offer_accepted")

    def test_04_default_get_validity(self):
        """Тест: проверка вычисления date_deadline в default_get"""

        values = (
            self.env["estate.property.offer"]
            .with_context(default_validity=7)
            .default_get(["validity", "date_deadline"])
        )

        expected_deadline = fields.Date.today() + timedelta(days=7)

        self.assertEqual(values["date_deadline"], expected_deadline, "date_deadline must be equal today + validity")
