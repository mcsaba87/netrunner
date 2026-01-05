class TestCaseValidationError(Exception):
    """Raised when a TestCase fails validation."""
    pass


class TestCaseValidator:
    # Required fields per testcase type
    REQUIRED_FIELDS = {
        "ping": {
            "name",
            "type",
            "dstAddr",
            "passOnFailure",
        },
        "http": {
            "name",
            "type",
            "dstAddr",
            "passOnFailure",
        },
        "udp": {
            "name",
            "type",
            "dstAddr",
            "dstPort",
            "passOnFailure",
        },
        "remote": {
            "name",
            "type",
            "dstAddr",
            "srcAddr",
            "aux",
            "passOnFailure",
        },
    }

    def validate(self, testcase):
        if not hasattr(testcase, "type"):
            raise TestCaseValidationError("TestCase is missing 'type' attribute")

        tc_type = testcase.type

        if tc_type not in self.REQUIRED_FIELDS:
            raise TestCaseValidationError(f"Unsupported testcase type '{tc_type}'")

        missing = self._missing_fields(testcase, self.REQUIRED_FIELDS[tc_type])

        if missing:
            raise TestCaseValidationError(
                f"TestCase '{getattr(testcase, 'name', '<unnamed>')}' "
                f"of type '{tc_type}' is missing required fields: "
                f"{', '.join(sorted(missing))}"
            )

        self._type_specific_checks(testcase)

        return True  # valid

    def _missing_fields(self, testcase, required_fields):
        missing = set()
        for field in required_fields:
            if not hasattr(testcase, field) or getattr(testcase, field) in (None, ""):
                missing.add(field)
        return missing

    def _type_specific_checks(self, testcase):
        """
        Optional deeper validation per type.
        Add more rules here without touching validate().
        """
        if testcase.type == "udp":
            if not isinstance(testcase.dstPort, int):
                raise TestCaseValidationError("udp testcase requires dstPort to be an integer")

        if testcase.type == "remote":
            if not isinstance(testcase.aux, str):
                raise TestCaseValidationError("remote testcase requires aux to be a JSON string")

        if hasattr(testcase, "passOnFailure"):
            if testcase.passOnFailure not in (0, 1):
                raise TestCaseValidationError("passOnFailure must be 0 or 1")
