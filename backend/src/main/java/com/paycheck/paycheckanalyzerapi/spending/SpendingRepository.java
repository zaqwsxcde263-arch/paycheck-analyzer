package com.paycheck.paycheckanalyzerapi.spending;

import com.paycheck.paycheckanalyzerapi.user.User;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface SpendingRepository extends JpaRepository<Spending, Long> {

    Optional<Spending> findByIdAndUser(Long id, User user);

    void deleteByIdAndUser(Long id, User user);

    @Query("""
            select s from Spending s
            where s.user = :user
              and (:from is null or s.date >= :from)
              and (:to is null or s.date <= :to)
              and (:categoryId is null or s.category.id = :categoryId)
            """)
    List<Spending> search(
            @Param("user") User user,
            @Param("from") LocalDate from,
            @Param("to") LocalDate to,
            @Param("categoryId") Long categoryId,
            Pageable pageable);

    List<Spending> findByUserAndDateBetweenOrderByDateAsc(User user, LocalDate from, LocalDate to);

    List<Spending> findTop10ByUserAndDateBetweenOrderByAmountDesc(User user, LocalDate from, LocalDate to);

    List<Spending> findByUserAndProductNameAndDateBetweenOrderByDateAsc(
            User user, String productName, LocalDate from, LocalDate to);
}

