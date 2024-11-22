ALTER TABLE BusinessCustomer
    ADD UNIQUE (`customer_id`);

ALTER TABLE IndividualCustomer
    ADD UNIQUE (`customer_id`);
