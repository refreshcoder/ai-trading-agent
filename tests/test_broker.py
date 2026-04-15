import pytest
from src.broker import PaperBroker
from src.models import LLMDecision


@pytest.fixture
def broker():
    return PaperBroker(initial_cash=100000.0)


def test_paper_broker_buy_success(broker):
    decision = LLMDecision(
        thought="",
        action="BUY",
        symbol="000001.SH",
        price_limit=10.0,
        volume=100)
    result = broker.execute(decision)
    assert result is True
    assert broker.cash == 99000.0  # 100000 - 1000
    assert broker.positions["000001.SH"]["volume"] == 100


def test_paper_broker_buy_insufficient_funds(broker):
    decision = LLMDecision(
        thought="",
        action="BUY",
        symbol="000001.SH",
        price_limit=1000.0,
        volume=200)  # needs 200000
    result = broker.execute(decision)
    assert result is False
    assert broker.cash == 100000.0
