package com.example.api_gateway.kafka

import org.apache.kafka.clients.consumer.ConsumerConfig
import org.apache.kafka.clients.producer.ProducerConfig
import org.apache.kafka.common.serialization.StringDeserializer
import org.apache.kafka.common.serialization.StringSerializer
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory
import org.springframework.kafka.core.*
import org.springframework.kafka.support.serializer.JsonDeserializer
import org.springframework.kafka.support.serializer.JsonSerializer

//@Configuration
class KafkaConfig {
//    @Value("\${spring.kafka.bootstrap-servers}")
//    private lateinit var bootstrapServers: String
//
//    @Bean
//    fun producerFactory(): ProducerFactory<String, Any>{
//        val configProps = mutableMapOf<String, Any>()
//        configProps[ProducerConfig.BOOTSTRAP_SERVERS_CONFIG] = bootstrapServers
//        configProps[ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG] = StringSerializer::class.java
//        configProps[ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG] = JsonSerializer::class.java
//
//        return DefaultKafkaProducerFactory(configProps)
//    }
//
//    @Bean
//    fun kafkaTemplate(): KafkaTemplate<String, Any>{
//        return KafkaTemplate(producerFactory())
//    }
//
//    @Bean
//    fun consumerFactory(): ConsumerFactory<String, Any> {
//        val props = mutableMapOf<String, Any>()
//        props[ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG] = bootstrapServers
//        props[ConsumerConfig.GROUP_ID_CONFIG] = "converter-service"
//        props[ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG] = StringDeserializer::class.java
//        props[ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG] = JsonDeserializer::class.java
//
//        return DefaultKafkaConsumerFactory(props)
//    }
//
//    @Bean
//    fun concurrentKafkaListenerContainerFactory(): ConcurrentKafkaListenerContainerFactory<String, Any> {
//        val factory = ConcurrentKafkaListenerContainerFactory<String, Any>()
//        factory.consumerFactory = consumerFactory()
//        return factory
//    }
}