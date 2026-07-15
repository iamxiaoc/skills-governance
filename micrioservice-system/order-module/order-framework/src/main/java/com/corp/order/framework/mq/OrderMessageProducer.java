package com.corp.order.framework.mq;

import com.corp.monitor.MonitorUtils;
import com.corp.trace.TraceContext;

/**
 * 订单消息生产者
 * FIXME: 该工具类为通用能力，不应放在模块framework中，应下沉到base-framework
 * 这是项目中实际存在的问题：通用MQ消息发送封装被放在了业务模块的framework中
 * 封装RocketMQ发送逻辑
 */
public class OrderMessageProducer {

    private final String topic;
    private final String producerGroup;

    public OrderMessageProducer(String topic, String producerGroup) {
        this.topic = topic;
        this.producerGroup = producerGroup;
    }

    /**
     * 发送订单创建消息
     */
    public boolean sendOrderCreateMessage(Long orderId, String orderData) {
        // 简化版：实际调用RocketMQ Producer发送消息
        String traceId = TraceContext.getTraceId();
        System.out.println("Send order create message: topic=" + topic + ", orderId=" + orderId + ", traceId=" + traceId);
        MonitorUtils.increment("mq.order.create.send");
        return true;
    }

    /**
     * 发送订单状态变更消息
     */
    public boolean sendOrderStatusChangeMessage(Long orderId, int oldStatus, int newStatus) {
        System.out.println("Send order status change: topic=" + topic + ", orderId=" + orderId + ", " + oldStatus + "->" + newStatus);
        return true;
    }

    /**
     * 发送延迟消息
     */
    public boolean sendDelayMessage(Long orderId, int delayLevel) {
        System.out.println("Send delay message: topic=" + topic + ", orderId=" + orderId + ", delayLevel=" + delayLevel);
        return true;
    }
}
