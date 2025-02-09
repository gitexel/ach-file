"""Tests ACH file builder."""

from unittest import TestCase

from ach.files import ACHFileBuilder, ACHFileContentsParser, NoBatchForTransactionError
from ach.record_types import (
    AddendaRecordType,
    BatchHeaderRecordType,
    EntryDetailRecordType,
)
from ach.record_types.record_fields import (
    AlphaNumFieldType,
    BlankPaddedRoutingNumberFieldType,
)
from ach.constants import AutoDateInput, BatchStandardEntryClassCode, TransactionCode
from tests import test_file


class TestDisplayRequiredKeys(TestCase):
    def setUp(self) -> None:
        self.ach_file_builder_class = ACHFileBuilder
        return super().setUp()

    def test_ach_file_builder_required_file_header_keys(self):
        test_required_keys = [
            "destination_routing",
            "origin_id",
            "destination_name",
            "origin_name",
        ]
        required_file_header_fields = (
            self.ach_file_builder_class.get_file_setting_fields(only_required=True)
        )
        self.assertListEqual(
            list(required_file_header_fields.keys()), test_required_keys
        )

    def test_ach_file_builder_all_file_header_keys(self):
        test_all_keys = [
            "record_type_code",
            "priority_code",
            "destination_routing",
            "origin_id",
            "file_creation_date",
            "file_creation_time",
            "file_id_modifier",
            "record size",
            "blocking_factor",
            "format_code",
            "destination_name",
            "origin_name",
            "reference_code",
        ]
        file_header_fields = self.ach_file_builder_class.get_file_setting_fields()
        self.assertListEqual(list(file_header_fields.keys()), test_all_keys)

    def test_ach_file_builder_required_batch_header_keys(self):
        test_req_keys = [
            "company_name",
            "company_identification",
            "company_entry_description",
        ]
        all_req_keys = [
            "company_name",
            "company_identification",
            "company_entry_description",
            "odfi_identification",
            "batch_number",
        ]
        required_fields = self.ach_file_builder_class.get_batch_fields(
            only_required=True
        )

        self.assertListEqual(list(required_fields.keys()), test_req_keys)
        self.assertListEqual(
            list(BatchHeaderRecordType.get_required_kwargs().keys()), all_req_keys
        )

    def test_ach_file_builder_all_batch_header_keys(self):
        test_all_keys = [
            "record_type_code",
            "service_class_code",
            "company_name",
            "company_discretionary_data",
            "company_identification",
            "standard_entry_class_code",
            "company_entry_description",
            "company_descriptive_date",
            "effective_entry_date",
            "settlement_date",
            "originator_status_code",
            "odfi_identification",
            "batch_number",
        ]
        all_fields = self.ach_file_builder_class.get_batch_fields()
        self.assertEqual(list(all_fields.keys()), test_all_keys)

    def test_ach_file_builder_required_entry_detail_keys(self):
        all_entry_detail_req_keys = [
            "transaction_code",
            "rdfi_routing",
            "rdfi_account_number",
            "amount",
            "individual_name",
            "trace_odfi_identifier",
            "trace_sequence_number",
        ]
        test_req_keys = [
            "transaction_code",
            "rdfi_routing",
            "rdfi_account_number",
            "amount",
            "individual_name",
        ]
        self.assertEqual(
            list(
                self.ach_file_builder_class.get_entry_fields(only_required=True).keys()
            ),
            test_req_keys,
        )
        self.assertEqual(
            list(EntryDetailRecordType.get_required_kwargs().keys()),
            all_entry_detail_req_keys,
        )

    def test_ach_file_builder_all_entry_detail_keys(self):
        test_all_keys = [
            "record_type_code",
            "transaction_code",
            "rdfi_routing",
            "rdfi_account_number",
            "amount",
            "individual_identification_number",
            "individual_name",
            "discretionary_data",
            "addenda_record_indicator",
            "trace_odfi_identifier",
            "trace_sequence_number",
        ]
        self.assertEqual(
            list(self.ach_file_builder_class.get_entry_fields().keys()), test_all_keys
        )

    def test_ach_file_builder_required_addenda_keys(self):
        self.assertEqual(
            list(
                self.ach_file_builder_class.get_addenda_fields(
                    only_required=True
                ).keys()
            ),
            [],
        )
        self.assertEqual(
            list(AddendaRecordType.get_required_kwargs().keys()),
            ["entry_detail_sequence_number"],
        )

    def test_ach_file_builder_all_addenda_keys(self):
        test_all_keys = [
            "record_type_code",
            "addenda_type_code",
            "payment_related_information",
            "addenda_sequence_number",
            "entry_detail_sequence_number",
        ]
        self.assertEqual(
            list(self.ach_file_builder_class.get_addenda_fields().keys()), test_all_keys
        )


class TestACHFileBuilder(TestCase):
    def setUp(self) -> None:
        self.ach_file_builder_class = ACHFileBuilder
        return super().setUp()

    def test_ach_file_builder(self):
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="102345678",
            destination_name="YOUR BANK",
            origin_name="YOUR FINANCIAL INSTITUTION",
        )
        b.add_batch(
            company_name="YOUR COMPANY",
            company_identification="1234567890",
            company_entry_description="Test",
            effective_entry_date=AutoDateInput.TOMORROW,
            standard_entry_class_code=BatchStandardEntryClassCode.CCD,
        )
        b.add_entries_and_addendas(
            [
                {
                    "transaction_code": TransactionCode.CHECKING_CREDIT,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                },
                {
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                },
                {
                    "transaction_code": 22,
                    "rdfi_routing": "023456789",
                    "rdfi_account_number": "45656565",
                    "amount": "7000",
                    "individual_name": "Mackey Shawnderson",
                    "addendas": [
                        {"payment_related_information": "Where's my money"},
                    ],
                },
            ]
        )
        parser = ACHFileContentsParser(b.render())
        ach_file_contents = parser.process_ach_file_contents(
            parser.process_records_list()
        )
        self.assertEqual(b.render(), ach_file_contents.render_file_contents())
        self.assertDictEqual(
            b.ach_file_contents.render_json_dict(), ach_file_contents.render_json_dict()
        )

    def test_ach_file_builder_multiple_batches(self):
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="102345678",
            destination_name="YOUR BANK",
            origin_name="YOUR FINANCIAL INSTITUTION",
        )
        b.add_batch(
            company_name="YOUR COMPANY",
            company_identification="1234567890",
            company_entry_description="Test",
            effective_entry_date=AutoDateInput.TOMORROW,
            standard_entry_class_code=BatchStandardEntryClassCode.CCD,
        )
        b.add_entries_and_addendas(
            [
                {
                    "transaction_code": 22,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                },
                {
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                },
                {
                    "transaction_code": 22,
                    "rdfi_routing": "023456789",
                    "rdfi_account_number": "45656565",
                    "amount": "7000",
                    "individual_name": "Mackey Shawnderson",
                    "addendas": [
                        {"payment_related_information": "Where's my money"},
                    ],
                },
            ]
        )
        b.add_batch(
            company_name="YOUR COMPANY",
            company_identification="1234567890",
            company_entry_description="Test 2",
            effective_entry_date=AutoDateInput.TOMORROW,
            standard_entry_class_code=BatchStandardEntryClassCode.PPD,
        )
        b.add_entries_and_addendas(
            [
                {
                    "transaction_code": 22,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                },
                {
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                },
                {
                    "transaction_code": 22,
                    "rdfi_routing": "023456789",
                    "rdfi_account_number": "45656565",
                    "amount": "7000",
                    "individual_name": "Mackey Shawnderson",
                    "addendas": [
                        {"payment_related_information": "Where's my money"},
                    ],
                },
            ]
        )

        parser = ACHFileContentsParser(b.render())
        ach_file_contents = parser.process_ach_file_contents(
            parser.process_records_list()
        )
        json_dict = b.ach_file_contents.render_json_dict()
        self.assertEqual(b.render(), ach_file_contents.render_file_contents())
        self.assertDictEqual(
            b.ach_file_contents.render_json_dict(), ach_file_contents.render_json_dict()
        )

        self.assertEqual(int(json_dict["file_control"]["batch_count"]), 2)
        self.assertEqual(int(json_dict["file_control"]["entry_and_addenda_count"]), 10)
        self.assertEqual(
            int(json_dict["file_control"]["entry_hash"]),
            int(json_dict["batches"][0]["batch_control"]["entry_hash"]) * 2,
        )

    def test_ach_file_builder_build_from_parser_output(self):
        parser = ACHFileContentsParser(test_file)
        ach_file_contents = parser.process_ach_file_contents(
            parser.process_records_list()
        )

        builder = self.ach_file_builder_class(
            **ach_file_contents.file_header_record.get_field_values()
        )
        for batch in ach_file_contents.batches:
            entry_dict_list = []
            for tx in batch.transactions:
                entry_dict = tx.entry.get_field_values()
                if tx.addendas:
                    entry_dict["addendas"] = [
                        addenda.get_field_values() for addenda in tx.addendas
                    ]
                entry_dict_list.append(entry_dict)

            builder.add_batch(
                **batch.batch_header_record.get_field_values()
            ).add_entries_and_addendas(entry_dict_list)

        self.assertEqual(test_file, builder.render())

    def test_add_transaction_before_batch(self):
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="102345678",
            destination_name="YOUR BANK",
            origin_name="YOUR FINANCIAL INSTITUTION",
        )
        with self.assertRaises(NoBatchForTransactionError):
            b.add_entries_and_addendas(
                [
                    {
                        "transaction_code": 22,
                        "rdfi_routing": "123456789",
                        "rdfi_account_number": "65656565",
                        "amount": "300",
                        "individual_name": "Janey Test",
                    },
                    {
                        "transaction_code": 27,
                        "rdfi_routing": "123456789",
                        "rdfi_account_number": "65656565",
                        "amount": "300",
                        "individual_name": "Janey Test",
                        "addendas": [
                            {
                                "payment_related_information": "Reversing the last transaction pls and thx"
                            },
                        ],
                    },
                    {
                        "transaction_code": 22,
                        "rdfi_routing": "023456789",
                        "rdfi_account_number": "45656565",
                        "amount": "7000",
                        "individual_name": "Mackey Shawnderson",
                        "addendas": [
                            {"payment_related_information": "Where's my money"},
                        ],
                    },
                ]
            )
        with self.assertRaises(NoBatchForTransactionError):
            b.add_entry_and_addenda(
                **{
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                }
            )

    def test_add_transaction_before_batch_raise_exc_false(self):
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="102345678",
            destination_name="YOUR BANK",
            origin_name="YOUR FINANCIAL INSTITUTION",
        )
        failed_entries = b.add_entries_and_addendas(
            [
                {
                    "transaction_code": 22,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                },
                {
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                },
                {
                    "transaction_code": 22,
                    "rdfi_routing": "023456789",
                    "rdfi_account_number": "45656565",
                    "amount": "7000",
                    "individual_name": "Mackey Shawnderson",
                    "addendas": [
                        {"payment_related_information": "Where's my money"},
                    ],
                },
            ],
            raise_exc=False,
        )
        self.assertEqual(len(failed_entries), 3)
        with self.assertRaises(NoBatchForTransactionError):
            b.add_entry_and_addenda(
                **{
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                }
            )

    def test_ach_file_builder_result_passes_parser_skips_entries(self):
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="102345678",
            destination_name="YOUR BANK",
            origin_name="YOUR FINANCIAL INSTITUTION",
        )
        b.add_batch(
            company_name="YOUR COMPANY",
            company_identification="1234567890",
            company_entry_description="Test",
            effective_entry_date=AutoDateInput.TOMORROW,
            standard_entry_class_code=BatchStandardEntryClassCode.CCD,
        )
        failed_entries = b.add_entries_and_addendas(
            [
                {
                    "transaction_code": TransactionCode.CHECKING_CREDIT,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "****6565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                },
                {
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                },
                {
                    "transaction_code": 39,
                    "rdfi_routing": "023456789",
                    "rdfi_account_number": "45656565",
                    "amount": "7000",
                    "individual_name": "Mackey Shawnderson",
                    "addendas": [
                        {"payment_related_information": "Where's my money"},
                    ],
                },
            ],
            raise_exc=False,
        )

        parser = ACHFileContentsParser(b.render())
        ach_file_contents = parser.process_ach_file_contents(
            parser.process_records_list()
        )
        self.assertEqual(b.render(), ach_file_contents.render_file_contents())
        self.assertDictEqual(
            b.ach_file_contents.render_json_dict(), ach_file_contents.render_json_dict()
        )
        self.assertEqual(len(failed_entries), 1, b.render())

    def test_add_transaction_to_nonexistent_batch(self):
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="102345678",
            destination_name="YOUR BANK",
            origin_name="YOUR FINANCIAL INSTITUTION",
        )
        b.add_batch(
            company_name="YOUR COMPANY",
            company_identification="1234567890",
            company_entry_description="Test",
            effective_entry_date=AutoDateInput.TOMORROW,
            standard_entry_class_code=BatchStandardEntryClassCode.CCD,
        )
        with self.assertRaises(IndexError):
            b.add_entries_and_addendas(
                [
                    {
                        "transaction_code": 22,
                        "rdfi_routing": "123456789",
                        "rdfi_account_number": "65656565",
                        "amount": "300",
                        "individual_name": "Janey Test",
                    },
                    {
                        "transaction_code": 27,
                        "rdfi_routing": "123456789",
                        "rdfi_account_number": "65656565",
                        "amount": "300",
                        "individual_name": "Janey Test",
                        "addendas": [
                            {
                                "payment_related_information": "Reversing the last transaction pls and thx"
                            },
                        ],
                    },
                    {
                        "transaction_code": 22,
                        "rdfi_routing": "023456789",
                        "rdfi_account_number": "45656565",
                        "amount": "7000",
                        "individual_name": "Mackey Shawnderson",
                        "addendas": [
                            {"payment_related_information": "Where's my money"},
                        ],
                    },
                ],
                batch_index=1,
            )

        with self.assertRaises(IndexError):
            b.add_entry_and_addenda(
                batch_index=1,
                **{
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                }
            )

    def test_ach_file_builder_for_custom_field_definition(self):
        """Tests to ensure use case for 10-digit file header odfi identification field is met."""
        self.ach_file_builder_class.file_header_record_type_class.field_definition_dict[
            "origin_id"
        ].field_type = AlphaNumFieldType
        b = self.ach_file_builder_class(
            destination_routing="012345678",
            origin_id="1234567890",
            destination_name="YOUR BANK",
            origin_name="YOUR COMPANY",
        )
        b.add_batch(
            company_name="YOUR COMPANY",
            company_identification="1234567890",
            company_entry_description="Test",
            effective_entry_date=AutoDateInput.TOMORROW,
            standard_entry_class_code=BatchStandardEntryClassCode.CCD,
        )
        b.add_entries_and_addendas(
            [
                {
                    "transaction_code": TransactionCode.CHECKING_CREDIT,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                },
                {
                    "transaction_code": 27,
                    "rdfi_routing": "123456789",
                    "rdfi_account_number": "65656565",
                    "amount": "300",
                    "individual_name": "Janey Test",
                    "addendas": [
                        {
                            "payment_related_information": "Reversing the last transaction pls and thx"
                        },
                    ],
                },
                {
                    "transaction_code": 22,
                    "rdfi_routing": "023456789",
                    "rdfi_account_number": "45656565",
                    "amount": "7000",
                    "individual_name": "Mackey Shawnderson",
                    "addendas": [
                        {"payment_related_information": "Where's my money"},
                    ],
                },
            ]
        )
        parser = ACHFileContentsParser(b.render())
        ach_file_contents = parser.process_ach_file_contents(
            parser.process_records_list()
        )
        self.assertEqual(b.render(), ach_file_contents.render_file_contents())
        self.assertDictEqual(
            b.ach_file_contents.render_json_dict(), ach_file_contents.render_json_dict()
        )
        self.ach_file_builder_class.file_header_record_type_class.field_definition_dict[
            "origin_id"
        ].field_type = BlankPaddedRoutingNumberFieldType
