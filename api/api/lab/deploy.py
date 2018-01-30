from typing import Dict, Any, List, Tuple

from threading import Thread
from cloudops import CloudOps
from models import CloudConfig, Slice, Scenario, Instance, NetworkNode, Router, Lab

from api.lab.helpers import randomword

from raven import Client
# Use sentry to send manually caught exceptions
sentry_raven = Client()


class DeployThread(Thread):
    """ Deployment thread"""

    def __init__(self, lab_id, cloudconfig_id, users):
        Thread.__init__(self)
        self.lab_id = lab_id
        self.cloudconfig_id = cloudconfig_id
        self.users = users

    def run(self):
        lab = Lab.fetchone(id=self.lab_id)
        cloudconfig = CloudConfig.fetchone(id=self.cloudconfig_id)
        cloudops = CloudOps(cloudconfig.provider, cloudconfig.detail)

        if cloudconfig.provider == 'AWS':
            """Create a new VPC (for AWS only)"""
            vpc_id, rt_id, ig_id = cloudops.ex_create_vpc(
                lab.name)
            new_detail = cloudconfig.detail
            new_detail['vpc_id'] = vpc_id
            new_detail['rt_id'] = rt_id
            new_detail['ig_id'] = ig_id
            cloudconfig.update(detail=new_detail.value)

        lab.update(status='deploying')

        try:
            """Chances are you are redeploying a lab, whose slices are already created"""
            slices = Slice.fetchall(lab_id=lab.id)

            """Otherwise, create slices for the lab"""
            if len(slices) == 0:
                for index, user in enumerate(self.users):
                    new_slice = Slice.insert(lab_id=lab.id, status='deploying', user_id=user['id'],
                                             name=lab.name + ' / slice_' + str(index), cloud_attrs={})
                    slices.append(new_slice)

            for sl in slices:
                if sl.status == 'deploying':
                    scenario = Scenario.fetchone(id=lab.scenario_id)
                    topo = scenario.topo

                    sec_group_id = cloudops.ex_create_security_group(sl.name)
                    new_cloud_attrs = sl.cloud_attrs
                    new_cloud_attrs['sec_group_id'] = sec_group_id
                    sl.update(cloud_attrs=new_cloud_attrs.value)

                    _create_networks(cloudops, sl, topo)
                    _create_instances(cloudops, sl, topo, sec_group_id)
                    _create_routers(cloudops, sl, topo, sec_group_id)
                    sl.update(status='active')
            lab.update(status='active')
        except Exception as ex:
            lab.update(status='deployfailed')
            # TODO: delete all deployed resources, so the deployment process can be restarted
            sentry_raven.captureException()


def _create_networks(cloudops: CloudOps, sl, topo):
    # Create networks
    for n in topo['networks']:
        new_net = NetworkNode.insert(
            name=n['name'], cidr=n['cidr'], status='deploying', x=n['x'], y=n['y'],
            slice_id=sl.id, gid=n['gid'])
        attrs = cloudops.create_network(new_net.name, new_net.cidr)
        new_net.update(cloud_attrs=attrs, status='active')


def _create_instances(cloudops: CloudOps, sl, topo, sec_group_id):
    # Prepare and save the instance models
    for s in topo['instances']:
        links = _extract_links(s, topo)
        configurations, password = _extract_configurations(s, topo)

        Instance.insert(
            name=s['name'],
            status='deploying', x=s['x'], y=s['y'],
            gid=s['gid'], slice_id=sl.id,
            image=s['image'],
            flavor=s['flavor'],
            links=links,
            configurations=configurations,
            password=password
        )

    # Actually deployment
    for instance in Instance.fetchall(slice_id=sl.id):
        ips = []
        nets = []
        for l in instance.links:
            ips.append(l['ip'])
            net = NetworkNode.fetchone(gid=l['network']['gid'], slice_id=sl.id)
            nets.append(net)

        public_ip, attrs = cloudops.create_instance(
            instance.name, nets, ips, instance.configurations, sec_group_id, instance.image, instance.flavor)
        instance.update(status='active', public_ip=public_ip, cloud_attrs=attrs)


def _create_routers(cloudops: CloudOps, sl, topo, sec_group_id):
    # Prepare and save the router models
    for s in topo['routers']:
        links = _extract_links(s, topo)
        configurations, password = _extract_configurations(s, topo)
        Router.insert(
            name=s['name'],
            status='deploying', x=s['x'], y=s['y'],
            gid=s['gid'], slice_id=sl.id,
            flavor=s['flavor'],
            configurations=configurations,
            password=password,
            links=links
        )

    # Actually deployment
    for router in Router.fetchall(slice_id=sl.id):
        ips = []
        nets = []
        for l in router.links:
            ips.append(l['ip'])
            net = NetworkNode.fetchone(gid=l['network']['gid'], slice_id=sl.id)
            nets.append(net)

        public_ip, attrs = cloudops.create_router(
                router.name, nets, ips, router.configurations, sec_group_id, router.flavor)
        router.update(status='active', public_ip=public_ip, cloud_attrs=attrs)


def _extract_links(instance: Dict[str, Any], topo: Dict[str, Any]) -> List:
    """extract links attached to an instance base on the topology"""
    links = []
    for l in topo['links']:
        if l['target']['gid'] == instance['gid']:
            links.append(l)
    return links


def _extract_configurations(instance: Dict[str, Any], topo: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """extract configurations of an instance base on the topology
    the extracted configurations is a dict of configuration name ('name') and and rendering parameters ('params')
    rendering parameters can be None"""
    configurations = []

    # configurations.append({"name": "staticroute", "params": _extract_static_route(instance, topo)})

    if instance['type'] == "Router":
        """ Get the number of interfaces """
        interfaces_count = sum(1 for link in topo['links'] if link['target']['gid'] == instance['gid'])
        configurations.append({"name": "shorewall", "params": {"interfaces_count": interfaces_count}})

    password = None

    for conf in instance['configurations']:
        if conf == "Enable password authentication" or conf == "noVNC":
            if password is None:
                password = randomword(8)
            configurations.append({"name": conf, "params": {"password": password}})
        else:
            configurations.append({"name": conf, "params": {}})

    return configurations, password


def _extract_static_route(instance: Dict[str, Any], topo: Dict[str, Any]) -> Dict[str, Any] :
    """Extract static route for an instance / router instance
    - TODO: implement me
    - TODO: check if _extract_static_route works with cases where there are more than one routers connected to an instance,
    in these cases, more than one static routes might be used
    the current code might work, but it needs to be checked anyway"""

    # get the networks to which the instance is connected
    connected_nets = []
    for link in topo['links']:
        if link['target']['gid'] == instance['gid']:
            connected_nets.append(link['network'])

    for net in connected_nets:
        # TODO: find the all routers, exclude the instance (if the instance is also a router)
        # routers = []
        pass


    # for each network, get the ip of the router and directly/indirectly connected cidrs

    return None