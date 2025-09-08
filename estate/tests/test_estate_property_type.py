from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class EstatePropertyTypeTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_partner = cls.env["res.partner"].create(
            {  # создание тестового партнера
                "name": "Test Buyer",
                "email": "buyer@test.com",
            }
        )

        cls.property_type = cls.env["estate.property.type"].create(
            {  # создание типа недвижимости
                "name": "Apartment"
            }
        )

        # Создаем недвижимость для оффера
        cls.test_property = cls.env["estate.property"].create(
            {
                "name": "Test Villa",
                "property_type_id": cls.property_type.id,
                "expected_price": 100000,
                "living_area": 50,
                "state": "new",
            }
        )

        # Создаем несколько тестовых офферов
        cls.offer = cls.env["estate.property.offer"].create(
            [
                {
                    "price": 100000,
                    "partner_id": cls.test_partner.id,
                    "validity": 7,
                    "status": "accepted",
                    "property_id": cls.test_property.id,
                },
                {
                    "price": 15000,
                    "partner_id": cls.test_partner.id,
                    "validity": 10,
                    "status": "refused",
                    "property_id": cls.test_property.id,
                },
            ]
        )

    def test_01_compute_offer_count(self):
        # проверка подсчета офферов для конкретного типа недвижимости

        property_type = self.property_type  # недвижимость, созданная в setUpClass

        # Вручную считаем, сколько офферов связано с этим property
        expected_count = sum(len(p.offer_ids) for p in property_type.property_ids)

        # Проверяем, что вычисляемое поле совпадает
        self.assertEqual(
            property_type.offer_count,
            expected_count,
            "offer_count типа недвижимости должен равняться числу всех связанных offer_ids",
        )
