package com.paycheck.paycheckanalyzerapi;

import com.paycheck.paycheckanalyzerapi.security.JwtProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(JwtProperties.class)
public class PaycheckAnalyzerApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(PaycheckAnalyzerApiApplication.class, args);
	}

}
