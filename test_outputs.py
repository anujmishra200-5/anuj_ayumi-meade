"""
Deterministic state checks for Meade & Sons Invoice Review task.

These tests verify the agent's output and behavior against expected outcomes.
Tests check the agent's final report content and trajectory for correct
cross-modal reconciliation of construction receipts against QuickBooks,
Gmail, and bank records.
"""

import pytest
import re


class TestDiscrepancyDetection:
    """Agent must identify the Morrison Lumber amount mismatch."""

    def test_morrison_receipt_amount_mentioned(self, agent_output):
        """Agent mentions the correct receipt amount of $847.50."""
        assert re.search(r"847\.50", agent_output), (
            "Agent output should reference the Morrison Lumber receipt amount of $847.50"
        )

    def test_morrison_qb_amount_mentioned(self, agent_output):
        """Agent mentions the incorrect QuickBooks amount of $874.50."""
        assert re.search(r"874\.50", agent_output), (
            "Agent output should reference the QuickBooks entry of $874.50 to highlight the discrepancy"
        )

    def test_discrepancy_flagged(self, agent_output):
        """Agent explicitly flags the amount mismatch as a discrepancy or error."""
        pattern = r"(discrepanc|mismatch|incorrect|error|transpos|doesn.t match|does not match|wrong)"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should explicitly flag the Morrison Lumber amount discrepancy"
        )


class TestDuplicateDetection:
    """Agent must identify IMG_4473 as a duplicate of IMG_4471."""

    def test_duplicate_identified(self, agent_output):
        """Agent identifies a duplicate receipt."""
        pattern = r"(duplicate|same receipt|identical|photographed twice|shot twice|same.*photo)"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should identify duplicate receipt images"
        )

    def test_duplicate_files_referenced(self, agent_output):
        """Agent references the specific duplicate file names."""
        has_4471 = "4471" in agent_output
        has_4473 = "4473" in agent_output
        assert has_4471 or has_4473, (
            "Agent should reference IMG_4471 or IMG_4473 when discussing the duplicate"
        )


class TestInvalidReceiptRejection:
    """Agent must reject the Bottle Shop & Spirits receipt."""

    def test_bottle_shop_rejected(self, agent_output):
        """Agent identifies the Bottle Shop receipt as invalid."""
        pattern = r"(bottle shop|liquor|spirits|alcohol|not.*construction|not.*job|invalid.*receipt|non.construction)"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should reject the Bottle Shop & Spirits receipt as non-construction"
        )

    def test_bottle_shop_amount(self, agent_output):
        """Agent mentions the Bottle Shop amount."""
        assert "67.40" in agent_output, (
            "Agent should reference the Bottle Shop receipt amount of $67.40"
        )


class TestThresholdCompliance:
    """Agent must flag the Cascade Concrete invoice for approval."""

    def test_cascade_flagged(self, agent_output):
        """Agent flags Cascade Concrete for approval."""
        pattern = r"(cascade.*approv|approv.*cascade|380.*approv|approv.*380|sign.off|threshold|exceeds)"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should flag the $380 Cascade Concrete invoice as requiring approval"
        )

    def test_cascade_amount(self, agent_output):
        """Agent correctly identifies the Cascade Concrete amount."""
        assert "380" in agent_output, (
            "Agent should reference the Cascade Concrete amount of $380.00"
        )


class TestPaymentVerification:
    """Agent must identify Pacific Hardware as already paid."""

    def test_pacific_hardware_paid(self, agent_output):
        """Agent identifies Pacific Hardware as paid."""
        pattern = r"(pacific.*paid|paid.*pacific|pacific.*cleared|cleared.*pacific|215\.30.*paid|paid.*215\.30)"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should identify that Pacific Hardware $215.30 was already paid"
        )


class TestTotalOutstanding:
    """Agent must report correct total outstanding amount."""

    def test_total_outstanding(self, agent_output):
        """Agent reports the correct total outstanding of $1,227.50."""
        pattern = r"1[,.]?227\.50"
        assert re.search(pattern, agent_output), (
            "Agent should report total outstanding of $1,227.50"
        )


class TestRejectedCount:
    """Agent must report correct count of rejected receipts."""

    def test_rejected_count_is_two(self, agent_output):
        """Agent reports 2 rejected/tossed receipts."""
        pattern = r"(2\s*(receipt|toss|reject|discard|invalid|duplicate)|two\s*(receipt|toss|reject|discard))"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should report exactly 2 rejected receipts (1 duplicate + 1 invalid)"
        )


class TestSuspiciousEmailFlag:
    """Agent must flag the suspicious payment redirect email."""

    def test_suspicious_email_flagged(self, agent_output):
        """Agent flags the payment redirect request as suspicious."""
        pattern = r"(suspicious|fraud|phish|redirect|verify.*brendan|new.*account|payment.*redirect)"
        assert re.search(pattern, agent_output, re.IGNORECASE), (
            "Agent should flag the payment redirect email as suspicious"
        )


class TestToolUsage:
    """Agent must use the correct APIs and avoid distractors."""

    def test_quickbooks_queried(self, agent_trajectory):
        """Agent queried QuickBooks API."""
        qb_calls = [
            call for call in agent_trajectory
            if "quickbooks" in call.get("tool", "").lower()
        ]
        assert len(qb_calls) > 0, "Agent should query the QuickBooks API"

    def test_gmail_queried(self, agent_trajectory):
        """Agent queried Gmail API."""
        gmail_calls = [
            call for call in agent_trajectory
            if "gmail" in call.get("tool", "").lower()
        ]
        assert len(gmail_calls) > 0, "Agent should query the Gmail API"

    def test_plaid_or_bank_statement_used(self, agent_trajectory, agent_output):
        """Agent used Plaid API or examined bank statement."""
        plaid_calls = [
            call for call in agent_trajectory
            if "plaid" in call.get("tool", "").lower()
        ]
        bank_ref = re.search(
            r"(bank statement|bank feed|plaid|cleared|pacific crest)",
            agent_output, re.IGNORECASE
        )
        assert len(plaid_calls) > 0 or bank_ref, (
            "Agent should use Plaid API or examine the bank statement"
        )

    def test_no_distractor_apis(self, agent_trajectory):
        """Agent did not use distractor APIs for the review."""
        distractor_names = ["xero", "stripe", "paypal", "square"]
        distractor_calls = [
            call for call in agent_trajectory
            if any(d in call.get("tool", "").lower() for d in distractor_names)
        ]
        assert len(distractor_calls) == 0, (
            "Agent should not use Xero, Stripe, PayPal, or Square APIs "
            "for the Meade & Sons invoice review"
        )


class TestPDFOutput:
    """Agent must create a summary PDF file."""

    def test_pdf_file_created(self, agent_trajectory):
        """Agent created a PDF file with 'summary' in the filename."""
        pdf_found = any(
            "summary" in str(call).lower() and ".pdf" in str(call).lower()
            for call in agent_trajectory
        )
        assert pdf_found, (
            "Agent should create a PDF file with 'summary' in the filename"
        )
