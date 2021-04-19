import pytest
import re
from settings import TEST_DATA
from suite.resources_utils import get_ingress_nginx_template_ts_conf
from suite.resources_utils import (
    wait_before_test,
    patch_deployment_from_yaml
)


@pytest.mark.ts
@pytest.mark.parametrize(
    "crd_ingress_controller, transport_server_setup",
    [
        (
            {
                "type": "complete",
                "extra_args":
                    [
                        "-enable-custom-resources",
                        "-global-configuration=nginx-ingress/nginx-configuration",
                        "-enable-leader-election=false"
                    ]
            },
            {"example": "transport-server-status", "app_type": "simple"},
        )
    ],
    indirect=True,
)
class TestTransportServerTcpLoadBalance:

    def restore_service(self, kube_apis, transport_server_setup) -> None:
        """
        Function to revert a TransportServer resource to a valid state.
        """
        dns_file = f"{TEST_DATA}/transport-server-tcp-load-balance/standard/dns.yaml"
        patch_deployment_from_yaml(kube_apis.apps_v1_api, transport_server_setup.namespace, dns_file)

    @pytest.mark.sean
    def test_number_of_replicas(
        self, kube_apis, crd_ingress_controller, transport_server_setup, ingress_controller_prerequisites
    ):
        """
        The load balancing of TCP should result in 3 servers to match the 3 replicas of a service.
        """
        dns_file = f"{TEST_DATA}/transport-server-tcp-load-balance/more-replicas.yaml"
        patch_deployment_from_yaml(kube_apis.apps_v1_api, transport_server_setup.namespace, dns_file)

        wait_before_test()

        result_conf = get_ingress_nginx_template_ts_conf(
            kube_apis.v1,
            transport_server_setup.namespace,
            transport_server_setup.name,
            transport_server_setup.ingress_pod_name,
            ingress_controller_prerequisites.namespace
        )

        pattern = 'server.*max_fails=1 fail_timeout=10s;'
        num_servers = len(re.findall(pattern, result_conf))

        assert num_servers is 3

        self.restore_service(kube_apis, transport_server_setup)
