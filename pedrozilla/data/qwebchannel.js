// qwebchannel.js mínimo (cliente JS de Qt WebChannel, LGPL-3.0, Qt Company)
"use strict";

var QWebChannelMessageTypes = {
    signal: 1,
    propertyUpdate: 2,
    init: 3,
    idle: 4,
    debug: 5,
    invokeMethod: 6,
    connectToSignal: 7,
    disconnectFromSignal: 8,
    setProperty: 9,
    response: 10,
};

var QWebChannel = function(transport, initCallback, converters) {
    if (typeof transport !== "object" || typeof transport.send !== "function") {
        console.error("QWebChannel expects a transport object");
        return;
    }
    var channel = this;
    this.transport = transport;
    this.execCallbacks = {};
    this.execId = 0;
    this.objects = {};
    this.send = function(data) {
        if (typeof(data) !== "string") data = JSON.stringify(data);
        channel.transport.send(data);
    };
    this.transport.onmessage = function(message) {
        var data = message.data;
        if (typeof data === "string") data = JSON.parse(data);
        switch (data.type) {
            case QWebChannelMessageTypes.signal: channel.handleSignal(data); break;
            case QWebChannelMessageTypes.response: channel.handleResponse(data); break;
            case QWebChannelMessageTypes.propertyUpdate: channel.handlePropertyUpdate(data); break;
            default: console.error("invalid message", message.data); break;
        }
    };
    this.exec = function(data, callback) {
        if (!callback) { channel.send(data); return; }
        if (channel.execId === Number.MAX_VALUE) channel.execId = Number.MIN_VALUE;
        if (data.hasOwnProperty("id")) return;
        data.id = channel.execId++;
        channel.execCallbacks[data.id] = callback;
        channel.send(data);
    };
    this.handleSignal = function(message) {
        var object = channel.objects[message.object];
        if (object) object.signalEmitted(message.signal, message.args);
        else console.warn("Unhandled signal: " + message.object + "::" + message.signal);
    };
    this.handleResponse = function(message) {
        if (!message.hasOwnProperty("id")) return;
        channel.execCallbacks[message.id](message.data);
        delete channel.execCallbacks[message.id];
    };
    this.handlePropertyUpdate = function(message) {
        message.data.forEach(function(data) {
            var object = channel.objects[data.object];
            if (object) object.propertyUpdate(data.signals, data.properties);
            else console.warn("Unhandled property update");
        });
        channel.exec({type: QWebChannelMessageTypes.idle});
    };
    channel.exec({type: QWebChannelMessageTypes.init}, function(data) {
        for (var name in data) { if (data.hasOwnProperty(name)) new QObject(name, data[name], channel); }
        for (var name2 in channel.objects) { if (channel.objects.hasOwnProperty(name2)) channel.objects[name2].unwrapProperties(); }
        if (initCallback) initCallback(channel);
        channel.exec({type: QWebChannelMessageTypes.idle});
    });
};
function QObject(name, data, webChannel) {
    this.__id__ = name;
    webChannel.objects[name] = this;
    this.__objectSignals__ = {};
    this.__propertyCache__ = {};
    var object = this;
    this.unwrapQObject = function(response) {
        if (response instanceof Array) return response.map(function(qobj){ return object.unwrapQObject(qobj); });
        if (!(response instanceof Object)) return response;
        if (!response["__QObject*__"] || response.id === undefined) {
            var jObj = {};
            for (var propName in response) { if (response.hasOwnProperty(propName)) jObj[propName] = object.unwrapQObject(response[propName]); }
            return jObj;
        }
        var objectId = response.id;
        if (webChannel.objects[objectId]) return webChannel.objects[objectId];
        if (!response.data) return;
        var qObject = new QObject(objectId, response.data, webChannel);
        if (qObject.destroyed && typeof qObject.destroyed.connect === "function") {
            qObject.destroyed.connect(function() {
                if (webChannel.objects[objectId] === qObject) {
                    delete webChannel.objects[objectId];
                    for (var k in qObject) if (qObject.hasOwnProperty(k)) delete qObject[k];
                }
            });
        }
        qObject.unwrapProperties();
        return qObject;
    };
    this.unwrapProperties = function() {
        for (var propIdx in object.__propertyCache__) {
            object.__propertyCache__[propIdx] = object.unwrapQObject(object.__propertyCache__[propIdx]);
        }
    };
    function addSignal(signalData, isPropertyNotifySignal) {
        var signalName = signalData[0];
        var signalIndex = signalData[1];
        object[signalName] = {
            connect: function(callback) {
                if (typeof(callback) !== "function") return;
                object.__objectSignals__[signalIndex] = object.__objectSignals__[signalIndex] || [];
                object.__objectSignals__[signalIndex].push(callback);
                if (isPropertyNotifySignal) return;
                if (object.__objectSignals__[signalIndex].length == 1) {
                    webChannel.exec({type: QWebChannelMessageTypes.connectToSignal, object: object.__id__, signal: signalIndex});
                }
            },
            disconnect: function(callback) {
                object.__objectSignals__[signalIndex] = (object.__objectSignals__[signalIndex] || []).filter(function(c){ return c != callback; });
                if (!isPropertyNotifySignal && object.__objectSignals__[signalIndex].length === 0) {
                    webChannel.exec({type: QWebChannelMessageTypes.disconnectFromSignal, object: object.__id__, signal: signalIndex});
                }
            }
        };
    }
    function invokeSignalCallbacks(signalName, signalArgs) {
        var connections = object.__objectSignals__[signalName];
        if (connections) connections.forEach(function(callback){ callback.apply(callback, signalArgs); });
    }
    this.propertyUpdate = function(signals, propertyMap) {
        for (var propertyIndex in propertyMap) {
            object.__propertyCache__[propertyIndex] = this.unwrapQObject(propertyMap[propertyIndex]);
        }
        for (var signalName in signals) invokeSignalCallbacks(signalName, signals[signalName]);
    };
    this.signalEmitted = function(signalName, signalArgs) {
        invokeSignalCallbacks(signalName, this.unwrapQObject(signalArgs));
    };
    function addMethod(methodData) {
        var methodName = methodData[0];
        var methodIdx = methodData[1];
        var invokedMethod = methodName[methodName.length - 1] === ')' ? methodIdx : methodName;
        object[methodName] = function() {
            var args = [], callback, errCallback;
            for (var i = 0; i < arguments.length; ++i) {
                var argument = arguments[i];
                if (typeof argument === "function") callback = argument;
                else args.push(argument);
            }
            var result;
            if (!callback && (typeof(Promise) === 'function')) {
              result = new Promise(function(resolve, reject){ callback = resolve; errCallback = reject; });
            }
            webChannel.exec({type: QWebChannelMessageTypes.invokeMethod, object: object.__id__, method: invokedMethod, args: args}, function(response) {
                if (response !== undefined) {
                    var res = object.unwrapQObject(response);
                    if (callback) callback(res);
                } else if (errCallback) errCallback();
            });
            return result;
        };
    }
    function bindGetterSetter(propertyInfo) {
        var propertyIndex = propertyInfo[0];
        var propertyName = propertyInfo[1];
        var notifySignalData = propertyInfo[2];
        object.__propertyCache__[propertyIndex] = propertyInfo[3];
        if (notifySignalData) {
            if (notifySignalData[0] === 1) notifySignalData[0] = propertyName + "Changed";
            addSignal(notifySignalData, true);
        }
        Object.defineProperty(object, propertyName, {
            configurable: true,
            get: function(){ return object.__propertyCache__[propertyIndex]; },
            set: function(value){
                object.__propertyCache__[propertyIndex] = value;
                webChannel.exec({type: QWebChannelMessageTypes.setProperty, object: object.__id__, property: propertyIndex, value: value});
            }
        });
    }
    data.methods.forEach(addMethod);
    data.properties.forEach(bindGetterSetter);
    data.signals.forEach(function(signal){ addSignal(signal, false); });
    Object.assign(object, data.enums);
}
QObject.prototype.toJSON = function(){ if (this.__id__ === undefined) return {}; return {id: this.__id__, "__QObject*__": true}; };
if (typeof module === 'object') { module.exports = {QWebChannel: QWebChannel}; }
