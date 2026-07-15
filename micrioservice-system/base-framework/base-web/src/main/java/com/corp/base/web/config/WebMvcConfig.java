package com.corp.base.web.config;

import com.corp.base.web.interceptor.BaseInterceptor;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

/**
 * Web MVC configuration for the base framework.
 *
 * <p>Registers the {@link BaseInterceptor}, a shared {@link ObjectMapper} and
 * a permissive-but-configurable CORS policy.
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    private final ObjectMapper objectMapper;

    public WebMvcConfig(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(baseInterceptor())
                .addPathPatterns("/**")
                .excludePathPatterns("/health", "/actuator/**", "/error");
    }

    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        // Prepend a Jackson converter sharing the global ObjectMapper so that
        // serialisation settings are consistent across the application.
        converters.add(0, new MappingJackson2HttpMessageConverter(objectMapper));
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/**")
                .allowedOriginPatterns("*")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
                .allowedHeaders("*")
                .exposedHeaders(BaseInterceptor.TRACE_ID_HEADER)
                .allowCredentials(true)
                .maxAge(3600);
    }

    @Bean
    public BaseInterceptor baseInterceptor() {
        return new BaseInterceptor();
    }
}
