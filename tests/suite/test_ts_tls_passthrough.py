import pytest, ssl
import requests
import subprocess
from suite.fixtures import PublicEndpoint
from suite.resources_utils import (
    wait_before_test,
    create_items_from_yaml,
    delete_items_from_yaml,
    wait_until_all_pods_are_ready,
)
from suite.custom_resources_utils import (
    read_ts,
    patch_ts,
    delete_ts,
    patch_ts_from_yaml,
)
from suite.yaml_utils import get_first_host_from_yaml
from suite.ssl_utils import get_server_certificate_subject, create_sni_session
from settings import TEST_DATA


class TransportServerTlsSetup:
    """
    Encapsulate Transport Server Example details.

    Attributes:
        name (str):
        namespace (str):
    """

    def __init__(self, public_endpoint: PublicEndpoint, name, namespace, ts_host):
        self.public_endpoint = public_endpoint
        self.name = name
        self.namespace = namespace
        self.ts_host = ts_host


@pytest.fixture(scope="class")
def transport_server_tls_passthrough_setup(
    request, kube_apis, test_namespace, ingress_controller_endpoint
) -> TransportServerTlsSetup:
    """
    Prepare Transport Server Example.

    :param request: internal pytest fixture to parametrize this method
    :param kube_apis: client apis
    :param test_namespace:
    :return: TransportServerSetup
    """
    print(
        "------------------------- Deploy Transport Server with tls passthrough -----------------------------------"
    )
    # deploy secure_app
    secure_app_file = f"{TEST_DATA}/{request.param['example']}/standard/secure-app.yaml"
    create_items_from_yaml(kube_apis, secure_app_file, test_namespace)

    # deploy transport server
    transport_server_file = f"{TEST_DATA}/{request.param['example']}/standard/transport-server.yaml"
    ts_resource = patch_ts_from_yaml(
        kube_apis.custom_objects, transport_server_file, test_namespace
    )
    ts_host = get_first_host_from_yaml(transport_server_file)
    wait_until_all_pods_are_ready(kube_apis.v1, test_namespace)

    def fin():
        print("Clean up TransportServer and app:")
        delete_ts(kube_apis.custom_objects, ts_resource, test_namespace)
        delete_items_from_yaml(kube_apis, secure_app_file, test_namespace)

    request.addfinalizer(fin)

    return TransportServerTlsSetup(
        ingress_controller_endpoint, ts_resource["metadata"]["name"], test_namespace, ts_host
    )


@pytest.mark.ts_tls
@pytest.mark.parametrize(
    "crd_ingress_controller, transport_server_tls_passthrough_setup",
    [
        (
            {
                "type": "complete",
                "extra_args": [
                    "-enable-custom-resources",
                    "-enable-leader-election=false",
                    "-enable-tls-passthrough=true",
                ],
            },
            {"example": "transport-server-tls-passthrough"},
        )
    ],
    indirect=True,
)
class TestTransportServerStatus:
    def restore_ts(self, kube_apis, transport_server_tls_passthrough_setup) -> None:
        """
        Function to revert a TransportServer resource to a valid state.
        """
        patch_src = f"{TEST_DATA}/transport-server-status/standard/transport-server.yaml"
        patch_ts(
            kube_apis.custom_objects,
            transport_server_tls_passthrough_setup.name,
            patch_src,
            transport_server_tls_passthrough_setup.namespace,
        )

    @pytest.mark.smoke
    def test_tls_passthrough(
        self, kube_apis, crd_ingress_controller, transport_server_tls_passthrough_setup
    ):
        session = create_sni_session()
        req_url = (
            f"https://{transport_server_tls_passthrough_setup.public_endpoint.public_ip}:"
            f"{transport_server_tls_passthrough_setup.public_endpoint.port_ssl}"
        )
        print(req_url)
        print(transport_server_tls_passthrough_setup.ts_host)
        wait_before_test()
        resp = session.get(
            req_url,
            headers={"host": transport_server_tls_passthrough_setup.ts_host},
            verify=False,
        )
        print(resp.status_code)
        print(resp.text)
        assert True
