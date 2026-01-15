import unittest

from ai_engine.schemas.pydantic.oracle_payload import WorkflowScreenPayload
from ai_engine.services.metadata_normalizer import (
    hydrate_oracle_metadata as normalize,
)
from ai_engine.services.raw_metadata_hydrator import (
    RawWorkflowScreenPayload,
    hydrate_oracle_metadata as hydrate_raw,
)


class TestRawMetadataHydrator(unittest.TestCase):
    def test_master_detail_required_length_and_unknown_tab_falls_back(self):
        raw = RawWorkflowScreenPayload.parse_obj(
            {
                "tab_ihm_wf": [
                    {
                        "id_tab": "SUPPLIER",
                        "type_tab": "M",
                        "load_tab": {
                            "columns": [
                                {"name": "ID", "type": "NUMBER", "required": True},
                                {"name": "EMAIL", "type": "VARCHAR2(50)", "required": True},
                            ],
                            "primaryKey": ["ID"],
                        },
                    },
                    {
                        "id_tab": "SUPPLIER_LINES",
                        "type_tab": "D",
                        "load_tab": {
                            "columns": [
                                {"name": "LINE_ID", "type": "NUMBER", "required": True}
                            ],
                            "primaryKey": ["LINE_ID"],
                        },
                    },
                ],
                "element_ihm_wf": [
                    {"id_element": "email", "type_element": "input_email"},
                    {"id_tab": "NO_SUCH_TAB", "id_element": "qty", "type_element": "input_number"},
                ],
            }
        )

        out = hydrate_raw(raw, id_client=1, id_wf="WF_TEST", id_tache="TASK", id_ihm="SCR")

        tabs = out["tab_ihm_wf"]
        master = next(t for t in tabs if t["TYPE_TAB"] == "M")
        detail = next(t for t in tabs if t["TYPE_TAB"] == "D")
        self.assertEqual(detail["ID_TAB_MAITRE"], master["ID_TAB"])

        elements = out["element_ihm_wf"]
        email = elements[0]
        self.assertEqual(email["ID_TAB"], master["ID_TAB"])
        self.assertEqual(email["ID_ELEMENT"], "EMAIL")
        self.assertEqual(email["LONGEUR_ELEMENT"], "50")
        self.assertTrue(email["VALIDATEUR_ELEMENT"]["required"])

        unknown = elements[1]
        self.assertEqual(unknown["ID_TAB"], master["ID_TAB"])
        self.assertEqual(unknown["POSITION_Y"], 2)

    def test_missing_load_tab_is_tolerated_and_detail_relations_are_derived(self):
        raw = RawWorkflowScreenPayload.parse_obj(
            {
                "tab_ihm_wf": [
                    {"id_tab": "PURCHASE_ORDER", "type_tab": "M"},
                    {"id_tab": "PO_DETAILS", "type_tab": "D"},
                ],
                "element_ihm_wf": [
                    {"id_tab": "PURCHASE_ORDER", "id_element": "ORDER_DATE", "type_element": "input_date"},
                ],
                # Non-Oracle shape: should not break hydration.
                "tab_detail_ihm_wf": [
                    {"id_master_table": "PURCHASE_ORDER", "id_detail_table": "PO_DETAILS"},
                ],
            }
        )

        out = hydrate_raw(raw, id_client=1, id_wf="WF", id_tache="TASK", id_ihm="SCR")

        tabs = out["tab_ihm_wf"]
        master = next(t for t in tabs if t["TYPE_TAB"] == "M")
        detail = next(t for t in tabs if t["TYPE_TAB"] == "D")
        self.assertEqual(detail["ID_TAB_MAITRE"], master["ID_TAB"])

        rels = out["tab_detail_ihm_wf"]
        self.assertTrue(any(r.get("ID_TAB") == detail["ID_TAB"] and r.get("ID_TAB_MAITRE") == master["ID_TAB"] for r in rels))

    def test_enum_values_coerces_objects(self):
        raw = RawWorkflowScreenPayload.parse_obj(
            {
                "tab_ihm_wf": [],
                "element_ihm_wf": [
                    {
                        "id_element": "STATUS",
                        "type_element": "select",
                        "enum_values": [{"value": "A"}, {"label": "B"}, {"name": "C"}, "D", 1],
                    }
                ],
            }
        )
        out = hydrate_raw(raw, id_client=1, id_wf="WF", id_tache="TASK", id_ihm="SCR")
        self.assertEqual(out["element_ihm_wf"][0]["ENUM_VALUES"], ["A", "B", "C", "D", "1"])


class TestMetadataNormalizer(unittest.TestCase):
    def test_supplier_list_derives_load_tab_from_elements(self):
        payload = WorkflowScreenPayload.parse_obj(
            {
                "tab_ihm_wf": [
                    {
                        "ID_TAB": "SUPPLIER",
                        "TYPE_TAB": "M",
                        "LOAD_TAB": {
                            "columns": [
                                {"name": "OLD_COL", "type": "NUMBER", "required": True},
                            ],
                            # Intentionally wrong: should be replaced with a guessed *_ID column.
                            "primaryKey": ["ID"],
                        },
                    }
                ],
                "element_ihm_wf": [
                    {
                        "ID_TAB": "SUPPLIER",
                        "ID_ELEMENT": "SUPPLIER_ID",
                        "TYPE_ELEMENT": "input_number",
                        "VALIDATEUR_ELEMENT": {"required": True},
                    },
                    {
                        "ID_TAB": "SUPPLIER",
                        "ID_ELEMENT": "SUPPLIER_EMAIL",
                        "TYPE_ELEMENT": "input_email",
                        "LONGEUR_ELEMENT": "50",
                        "VALIDATEUR_ELEMENT": {"required": True},
                    },
                    {
                        "ID_TAB": "SUPPLIER",
                        "ID_ELEMENT": "SUPPLIER_PHONE",
                        "TYPE_ELEMENT": "tel",
                        "LONGEUR_ELEMENT": "20",
                        "VALIDATEUR_ELEMENT": {"required": False},
                    },
                    # Non-data controls: should NOT become columns.
                    {"ID_TAB": "SUPPLIER", "ID_ELEMENT": "SEARCH", "TYPE_ELEMENT": "input_text"},
                    {"ID_TAB": "SUPPLIER", "ID_ELEMENT": "SAVE_BUTTON", "TYPE_ELEMENT": "button"},
                    {"ID_TAB": "SUPPLIER", "ID_ELEMENT": "PAGINATION", "TYPE_ELEMENT": "pagination"},
                ],
                "tab_detail_ihm_wf": [],
            }
        )

        normalized = normalize(payload, id_client=1, id_wf="WF", id_tache="TASK", id_ihm="SUPPLIER_LIST")

        tab = normalized.tab_ihm_wf[0]
        load_tab = tab.load_tab or {}
        columns = load_tab.get("columns") or []

        col_names = {c["name"] for c in columns}
        self.assertEqual(
            col_names,
            {"SUPPLIER_ID", "SUPPLIER_EMAIL", "SUPPLIER_PHONE"},
        )

        by_name = {c["name"]: c for c in columns}
        self.assertEqual(by_name["SUPPLIER_ID"]["type"], "NUMBER")
        self.assertEqual(by_name["SUPPLIER_EMAIL"]["type"], "VARCHAR2(50)")
        self.assertEqual(by_name["SUPPLIER_PHONE"]["type"], "VARCHAR2(20)")

        self.assertTrue(by_name["SUPPLIER_ID"]["required"])
        self.assertTrue(by_name["SUPPLIER_EMAIL"]["required"])
        self.assertFalse(by_name["SUPPLIER_PHONE"]["required"])

        self.assertEqual(load_tab.get("primaryKey"), ["SUPPLIER_ID"])
        self.assertIn("CREATE TABLE SUPPLIER", load_tab.get("sql_ddl") or "")

    def test_bad_values_are_coerced_and_master_detail_is_linked(self):
        payload = WorkflowScreenPayload.parse_obj(
            {
                "tab_ihm_wf": [
                    {"ID_TAB": "master tab", "TYPE_TAB": "T", "LOAD_TAB": {"columns": [], "primaryKey": ["ID"]}},
                    {"ID_TAB": "detail tab", "TYPE_TAB": "D", "LOAD_TAB": {"columns": [], "primaryKey": ["ID"]}},
                ],
                "element_ihm_wf": [
                    {"ID_TAB": "master tab", "ID_ELEMENT": "SEARCH", "TYPE_ELEMENT": "null", "ACTIVE": "T", "TRANSIT": "T"},
                    {"ID_TAB": "master tab", "ID_ELEMENT": "PAGINATION", "TYPE_ELEMENT": "null"},
                ],
                "tab_detail_ihm_wf": [],
            }
        )

        normalized = normalize(payload, id_client=1, id_wf="WF", id_tache="TASK", id_ihm="SCR")

        master = next(t for t in normalized.tab_ihm_wf if t.type_tab == "M")
        detail = next(t for t in normalized.tab_ihm_wf if t.type_tab == "D")
        self.assertEqual(detail.id_tab_maitre, master.id_tab)

        search = next(e for e in normalized.element_ihm_wf if e.id_element == "SEARCH")
        self.assertEqual(search.type_element, "input_text")
        self.assertEqual(search.active, "O")
        self.assertEqual(search.transit, "N")

        pagination = next(e for e in normalized.element_ihm_wf if e.id_element == "PAGINATION")
        self.assertEqual(pagination.type_element, "pagination")
        self.assertEqual(search.position_y, 1)
        self.assertEqual(pagination.position_y, 2)

        master_load_tab = master.load_tab or {}
        self.assertEqual(master_load_tab.get("columns"), [])
        self.assertEqual(master_load_tab.get("primaryKey"), [])
