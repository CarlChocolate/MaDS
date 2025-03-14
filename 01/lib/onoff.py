# Create nodes
nodes = ns.NodeContainer()
nodes.Create(2)

# Create point-to-point helper
pointToPoint = ns.PointToPointHelper()
pointToPoint.SetDeviceAttribute("DataRate", ns.StringValue("5Mbps"))
pointToPoint.SetChannelAttribute("Delay", ns.StringValue("2ms"))

# Install devices
devices = pointToPoint.Install(nodes)

# Install Internet stack
stack = ns.InternetStackHelper()
stack.Install(nodes)

# Assign IP addresses
address = ns.Ipv4AddressHelper()
address.SetBase(ns.Ipv4Address("10.1.1.0"), ns.Ipv4Mask("255.255.255.0"))
interfaces = address.Assign(devices)

# Create OnOff Application
port = 9
onoff = ns.OnOffHelper(
    "ns3::UdpSocketFactory",
    ns.Address(ns.InetSocketAddress(interfaces.GetAddress(1), port).ConvertTo()),
)

# Set OnOff attributes
onoff.SetAttribute(
    "OnTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=0.3]")
)
onoff.SetAttribute(
    "OffTime", ns.StringValue("ns3::ConstantRandomVariable[Constant=0.7]")
)
onoff.SetAttribute("DataRate", ns.StringValue("1Mbps"))
onoff.SetAttribute("PacketSize", ns.UintegerValue(1024))

# Install application on node 0
app = onoff.Install(nodes.Get(0))
app.Start(ns.Seconds(1.0))
app.Stop(ns.Seconds(10.0))

# Create packet sink on receiver
sink = ns.PacketSinkHelper(
    "ns3::UdpSocketFactory",
    ns.Address(ns.InetSocketAddress(ns.Ipv4Address.GetAny(), port).ConvertTo()),
)
sink_app = sink.Install(nodes.Get(1))
sink_app.Start(ns.Seconds(0.0))
sink_app.Stop(ns.Seconds(11.0))

# Enable logging
ns.LogComponentEnable("OnOffApplication", ns.LOG_LEVEL_INFO)
ns.LogComponentEnable("PacketSink", ns.LOG_LEVEL_INFO)

# Run simulation
ns.Simulator.Stop(ns.Seconds(11.0))
ns.Simulator.Run()
ns.Simulator.Destroy()
