from custom_components.launtel import const


def test_constants_values():
    assert const.DOMAIN == "launtel"
    assert const.DEFAULT_NAME == "Launtel"
    assert const.CONF_USERNAME == "username"
    assert const.CONF_PASSWORD == "password"
    assert const.CONF_SERVICE_ID == "service_id"
    assert const.PLATFORMS == ["button", "select", "sensor"]
