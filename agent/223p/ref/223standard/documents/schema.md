# 223 Schema

The principal object in this schema is a _device_ which is a tangible object
designed to accomplish a specific task.  Devices are connected to each other to
form a _system_, which in turn may be grouped together to form other systems.
Devices may have one or more _parts_ which can provide additional
details of the composition of the device.

* contains - links a system to one of its devices
* isContainedIn - links a device to the system that contains it

Containment relationships between systems are refined by these properties:

* hasSubsystem - links a system to one of its subsystems (subproperty of contains)
* isSubsystemOf - links a system to its supersystem (inverse hasSubsystem,
    subproperty of isContainedIn)

Containment relationships between systems and devices are refined by these
properties:

* hasDevice - links a system to one of its subsystems (subproperty of contains)
* isDeviceOf - links a device to its system (inverse hasDevice, subproperty of
    isContainedIn)

Containment relationships between devices and their constituent parts are
refined by these properties:

* hasPart - Relationship between a part and its parent part or device
    (subproperty of contains)
* isPartOf - inverse of hasPart (subproperty of isContainedIn)

## System

A collection of connected devices or other systems.

## Device

A tangible object designed to accomplish a specific task.

Devices may be connected to other devices. Connected devices interact in some
ways.

* connectedTo - links a device or system to another device or system
* connectedFrom - links a device or system to another device or system
    from which it is connected to (inverse of connectedTo)

Devices have connection points that describe a way a device can be connected
to another device.

* hasConnectionPoint - links a device or system to one of its connection points
* connectedThrough - links a device or system to a connection through which it
    is connected to other devices or systems by one of its connection points

Devices may have parts that contribute to its function.

## Connection

Qualifies the connectedTo property between systems or devices.

Two or more connected systems or devices are connected through a connection.

* connectsTo - links a connection to one of the device or systems it connects
* connectedAt - links a connection to one of the connection points of the
    device to which is connects devices

## ConnectionPoint

A connection point belongs to exactly one device. Any device connected through
a connection is connected at one of its connection points to the connection.

* connectsThrough - links a connection point to the connection through which
    it connects its device or system
* isConnectionPointOf - links a connection point to its device

## Part

A tangible object designed to be combined with other parts to refine the
composition of a Device.

## Property

An attribute, quality, or characteristic of a feature of interest.

* hasProperty - links a feature of interest to a property
* isPropertyOf - inverse of hasProperty
* hasValue - link from a Property to a Value

### QuantifiableProperty

A property that can be quantified.

* hasQuantityKind - reference to qudt:QuantityKind (i.e., quantitykind:Temperature)
* hasUnits - reference to qudt:Unit (i.e., unit:DEG_C)

The `hasQuantityKind` property is required.

If the `hasUnits` property is provided then all of the Value instances (a) do
not have a `hasUnits` property which implies that they are all the one
associated with the property, or (b) if they do then the property is identical,
e.g., both the Property and its associated Value instances reference
`unit:DEG_C`.

If the `hasUnits` property is not provided, all of the Value instances must
have a `hasUnits` property that is of the correct quantity kind, and the query
engine is responsible for mapping the provided values to the expected values,
e.g., `unit:DEG_C` is expected by `unit:DEG_F` is provided.

### ObservableProperty

A subclass of Property, the value of the property is the result of a controller
reading a sensor or calculating (see also [sosa:ObservableProperty](https://www.w3.org/TR/vocab-ssn/#SOSAObservableProperty))

* observes - link from an object/register reference to a property
* isObservedBy - link from the property to the object/register reference where
    it gets its value

### ActuatableProperty

A subclass of Property, the value of the property is the result of a controller
reading a sensor or calculating (see also [sosa:ActuatableProperty](https://www.w3.org/TR/vocab-ssn/#SOSAActuatableProperty))

* actuatesProperty - link from an object/register to a property
* isActuatedBy - link from the property to the object/register where it gets
    its value

## Value

A representation of a value of a property (see also qudt:Quantity)

* hasTimestamp - datetime (see also [sosa:resultTime](https://www.w3.org/TR/vocab-ssn/#SOSAresultTime))
* hasSimpleValue - literal value (see also qudt:quantityValue, [sosa:hasSimpleResult](https://www.w3.org/TR/vocab-ssn/#SOSAhasSimpleResult))
* hasUnits - reference to qudt:Unit (i.e., unit:DEG_C)
* isValueOf - reference to a property, inverse of hasValue
