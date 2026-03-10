package com.paycheck.paycheckanalyzerapi.category;

import com.paycheck.paycheckanalyzerapi.user.User;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CategoryRepository extends JpaRepository<Category, Long> {

    @Query("select c from Category c where c.user is null or c.user = :user order by c.name asc")
    List<Category> findAllForUserOrGlobal(@Param("user") User user);
}

