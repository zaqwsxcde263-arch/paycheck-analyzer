package com.paycheck.paycheckanalyzerapi.auth;

import com.paycheck.paycheckanalyzerapi.auth.dto.LoginRequest;
import com.paycheck.paycheckanalyzerapi.auth.dto.LoginResponse;
import com.paycheck.paycheckanalyzerapi.auth.dto.RegisterRequest;
import com.paycheck.paycheckanalyzerapi.auth.dto.RegisterResponse;
import com.paycheck.paycheckanalyzerapi.security.JwtTokenService;
import com.paycheck.paycheckanalyzerapi.user.User;
import com.paycheck.paycheckanalyzerapi.user.UserRepository;
import java.time.OffsetDateTime;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenService jwtTokenService;
    private final AuthenticationManager authenticationManager;

    public AuthService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenService jwtTokenService,
            AuthenticationManager authenticationManager) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenService = jwtTokenService;
        this.authenticationManager = authenticationManager;
    }

    @Transactional
    public RegisterResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email is already registered");
        }

        User user = new User();
        user.setName(request.getName());
        user.setEmail(request.getEmail());
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setCreatedAt(OffsetDateTime.now());

        userRepository.save(user);

        String token = jwtTokenService.generateToken(user);

        RegisterResponse response = new RegisterResponse();
        response.setId(user.getId());
        response.setName(user.getName());
        response.setEmail(user.getEmail());
        response.setToken(token);
        return response;
    }

    public LoginResponse login(LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword()));

        User user = (User) authentication.getPrincipal();
        String token = jwtTokenService.generateToken(user);

        LoginResponse.UserSummary summary = new LoginResponse.UserSummary();
        summary.setId(user.getId());
        summary.setName(user.getName());
        summary.setEmail(user.getEmail());

        LoginResponse response = new LoginResponse();
        response.setToken(token);
        response.setUser(summary);
        return response;
    }
}

