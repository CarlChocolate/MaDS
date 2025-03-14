import ctypes
import os
import json
from typing import Union

from ns import ns

"""
# enable logging on applications
ns.LogComponentEnable("UdpEchoClientApplication", ns.LOG_LEVEL_INFO)
ns.LogComponentEnable("UdpEchoServerApplication", ns.LOG_LEVEL_INFO)
ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()
"""

def get_address_table_from_iface_container(
    ifaces: ns.Ipv4InterfaceContainer,
    display: bool = True,
) -> dict:
    """
    Extract address information from an IPv4 interface container and create a table of addresses.

    Parameters
    ----------
    ifaces : ns.Ipv4InterfaceContainer
        Container of IPv4 interfaces from which to extract address information.
    display : bool, optional
        If True, prints the address table in JSON format. Default is True.

    Returns
    -------
    list[dict]
        A list of dictionaries containing address information for each interface.
        Each dictionary contains:
            - 'iface': Interface index
            - 'address_stack': Address stack index
            - 'address': IPv4 address string
            - 'broadcast': Broadcast address string
            - 'netmask': Network mask string

    Notes
    -----
    This function iterates through all interfaces in the container and their
    associated addresses to create a comprehensive table of network addressing
    information.

    Examples
    --------
    >>> ifaces = ns.Ipv4InterfaceContainer()
    >>> address_table = get_address_table_from_iface_container(ifaces)
    >>> address_table = get_address_table_from_iface_container(ifaces, display=False)
    """
    address_table = []
    n_ifaces = ifaces.GetN()

    for i in range(n_ifaces):
        iface_ptr, iface_idx = ifaces.Get(i)
        ipv4l3 = iface_ptr.__deref__()
        n_addresses = ipv4l3.GetNAddresses(iface_idx)

        for j in range(n_addresses):
            address_stack = ipv4l3.GetAddress(iface_idx, j)
            address_table.append(
                {
                    "iface": i,
                    "address_stack": j,
                    "address": str(address_stack.GetAddress()),
                    "broadcast": str(address_stack.GetBroadcast()),
                    "netmask": str(address_stack.GetMask()),
                }
            )

    if display:
        print(json.dumps(address_table, indent=2))

    return address_table

def get_device_mac_address(device: Union[ns.NetDevice, ns.Ptr]) -> ns.Mac48Address:
    """
    Get the MAC address of a network device.

    Parameters
    ----------
    device : ns.Device
        The network device object from which to extract the MAC address.

    Returns
    -------
    ns.Mac48Address
        The MAC address of the device in ns3 Mac48Address format.

    Notes
    -----
    This function converts the generic address obtained from the device
    to a specific Mac48Address format used in ns-3.
    """

    # Ensure that device is a NetDevice
    try:
        device = device.__deref__()
    except AttributeError as e:
        # device is already a NetDevice
        pass

    address = device.GetAddress()
    return ns.Mac48Address.ConvertFrom(address)

def get_nodeid_in_nodelist(device: Union[ns.NetDevice, ns.Ptr]) -> int:
    """
    Get the node ID from a device object.

    Parameters
    ----------
    device : ns.Device
        The network device object from which to extract the node ID.

    Returns
    -------
    int
        The unique identifier (ID) of the node associated with the device.

    Notes
    -----
    This function first gets the node pointer from the device,
    dereferences it to get the actual node object, and then
    retrieves its ID.
    """

    # Ensure that device is a NetDevice
    try:
        device = device.__deref__()
    except AttributeError as e:
        # device is already a NetDevice
        pass

    node_pointer = device.GetNode()
    node = node_pointer.__deref__()
    return node.GetId()

def get_iface_from_ifacecontainer(
    container: ns.Ipv4InterfaceContainer, if_idx: int
) -> ns.Ipv4Interface:
    """
    Retrieves an interface from an Ipv4InterfaceContainer.

    Parameters
    ----------
    container : ns.Ipv4InterfaceContainer
        The container from which the interface is to be retrieved.
    if_idx : int
        The index of the interface in the container.

    Returns
    -------
    ns.Ipv4Interface
        The retrieved interface.
    """
    ipproto, idx = container.Get(if_idx)
    ipproto = ipproto.__deref__()
    iface = ipproto.GetInterface(idx).__deref__()
    return iface


def assign_ip_to_iface(
    device: Union[ns.NetDevice, ns.Ptr], addr: str, netmask: str
) -> bool:
    """
    Assigns an IP address to a device.

    Parameters
    ----------
    device : Union[ns.NetDevice, ns.Ptr]
        The device to which the IP address will be assigned.
    addr : str
        The IP address to be assigned.
    netmask : str
        The netmask for the IP address.

    Returns
    -------
    bool
        True if the IP address was successfully assigned, False otherwise.
    """

    # Ensure that device is a NetDevice
    try:
        device = device.__deref__()
    except AttributeError as e:
        # device is already a NetDevice
        pass

    # Get the node
    node = device.GetNode().__deref__()
    # Get Ipv4 object for node
    ip = node.GetObject[ns.Ipv4]().__deref__()
    # Check if there is an interface with ip stack on device
    if_index = ip.GetInterfaceForDevice(device)
    if if_index == -1:
        if_index = ip.AddInterface(device)

    # Assign ip address
    status = ip.AddAddress(
        if_index,
        ns.Ipv4InterfaceAddress(
            ns.Ipv4Address(addr), ns.Ipv4Mask(netmask)
        ),
    )

    return status

def assign_ip_to_device(
    device: Union[ns.NetDevice, ns.Ptr],
    addr: str,
    netmask: Union[str, int],
) -> bool:
    """
    Assign an IPv4 address and netmask to a network device.

    Parameters
    ----------
    device : Union[ns.NetDevice, ns.Ptr]
        The network device or a pointer to the network device to which
        the IP address will be assigned.
    addr : str
        The IPv4 address to assign to the device in string format
        (e.g., '192.168.1.1').
    netmask : Union[str, int]
        The network mask either as a string (e.g., '255.255.255.0')
        or as an integer representing the prefix length (e.g., 24).

    Returns
    -------
    bool
        True if the IP address was successfully assigned to the device,
        False otherwise.

    Notes
    -----
    This function handles both direct NetDevice objects and pointers to
    NetDevice objects. If a pointer is provided, it will be dereferenced
    automatically. The function creates an IPv4 interface, adds the specified
    address with netmask, and attaches it to the device.

    Examples
    --------
    >>> assign_ip_to_device(device, "192.168.1.1", "255.255.255.0")
    True
    >>> assign_ip_to_device(device, "10.0.0.1", 24)
    True
    """
    # Ensure that device is a NetDevice
    try:
        device = device.__deref__()
    except AttributeError:
        # device is already a NetDevice
        pass

    iface = ns.Ipv4Interface()
    iface.AddAddress(
        ns.Ipv4InterfaceAddress(
            ns.Ipv4Address(addr),
            ns.Ipv4Mask(netmask),
        )
    )
    status = iface.SetDevice(device)

    return status



def get_ipproto_on_node(node: Union[ns.Node, ns.Ptr]) -> ns.Ipv4L3Protocol:
    """
    Returns the Ipv4L3Protocol object for a node.

    Parameters
    ----------
    node : Union[ns.Node, ns.Ptr]
        The node for which the Ipv4L3Protocol object is to be returned.

    Returns
    -------
    ns.Ipv4L3Protocol
        The Ipv4L3Protocol object for the node.
    """
    # Ensure that node is a Node and not a pointer
    try:
        node = node.__deref__()
    except AttributeError as e:
        pass

    return node.GetObject[ns.Ipv4]().__deref__()


def create_echo_client_helper(
    server_address: str,
    server_port: int,
    max_packets: int = 50,
    interval: float = 1.0,
    packet_size: int = 1500,
) -> ns.UdpEchoClientHelper:
    """
    Creates a UdpEchoClientHelper object.

    Parameters
    ----------
    server_address : str
        The server address for the UdpEchoClientHelper.
    server_port : int
        The server port for the UdpEchoClientHelper.
    max_packets : int, optional
        The maximum number of packets for the UdpEchoClientHelper, by default 50.
    interval : float, optional
        The interval for the UdpEchoClientHelper, by default 1.0.
    packet_size : int, optional
        The packet size for the UdpEchoClientHelper, by default 1500.

    Returns
    -------
    ns.UdpEchoClientHelper
        The created UdpEchoClientHelper object.
    """

    remote = ns.Address(
        ns.InetSocketAddress(
            ns.Ipv4Address(server_address),
            server_port
        ).ConvertTo()
    )
    echo_client = ns.UdpEchoClientHelper(remote)
    echo_client.SetAttribute("MaxPackets", ns.UintegerValue(max_packets))
    echo_client.SetAttribute("Interval", ns.TimeValue(ns.Seconds(interval)))
    echo_client.SetAttribute("PacketSize", ns.UintegerValue(packet_size))
    return echo_client


def get_routing_table_str(node: Union[ns.Node, ns.Ptr]) -> str:
    """
    Retrieves the routing table for a node and returns it as a string.
    This function uses ns-3 internal PrintRoutingTable method.
    However, as this method only works with files, we provide it with
    temporary name and the file is then read to memory and deleted.

    Parameters
    ----------
    node : Union[ns.Node, ns.Ptr]
        The node for which the routing table is to be returned.

    Returns
    -------
    str
        The routing table for the node.
    """
    try:
        node = node.__deref__()
    except AttributeError as e:
        pass

    tmpfname = ".routing"
    ipproto = node.GetObject[ns.Ipv4]().__deref__()
    routing_proto = ipproto.GetRoutingProtocol().__deref__()
    routing_stream = ns.OutputStreamWrapper(tmpfname, 0)
    routing_proto.PrintRoutingTable(routing_stream)

    with open(tmpfname, "r") as f:
        routing_table = f.read()
    os.remove(tmpfname)
    return routing_table


def get_routing_table(node: Union[ns.Node, ns.Ptr]) -> list:
    """
    Returns the routing table for a node.

    Parameters
    ----------
    node : Union[ns.Node, ns.Ptr]
        The node for which the routing table is to be returned.

    Returns
    -------
    list
        The routing table for the node.
    """
    try:
        node = node.__deref__()
    except AttributeError as e:
        pass

    ipv4 = node.GetObject[ns.Ipv4]()
    routes = []
    if ipv4:
        list_routing = ipv4.GetRoutingProtocol().GetObject[ns.Ipv4ListRouting]()

        # Iterate through each routing protocol in the list
        for i in range(list_routing.GetNRoutingProtocols()):
            priority = ctypes.c_int16()
            routing_protocol = list_routing.GetRoutingProtocol(i, priority)

            # Check if the routing protocol provides a GetNRoutes function
            # This is true for Ipv4StaticRouting, but may vary for other protocols
            if hasattr(routing_protocol, "GetNRoutes"):
                num_routes = routing_protocol.GetNRoutes()

                for j in range(num_routes):
                    route = routing_protocol.GetRoute(j)
                    dest = route.GetDest()
                    gateway = route.GetGateway()
                    interface = route.GetInterface()
                    routes.append(dict(dest=dest, gateway=gateway, interface=interface))
    return routes


def stringify_routing_table(routing_table: list[dict]) -> list[str]:
    """
    Converts a routing table to a list of strings.

    Parameters
    ----------
    routing_table : list[dict]
        The routing table to be converted.

    Returns
    -------
    list[str]
        The converted routing table.
    """
    rt = []
    for i in routing_table:
        rt.append(
            f"dest: {i['dest']}, gateway: {i['gateway']}, interface: {i['interface']}"
        )

    return rt
