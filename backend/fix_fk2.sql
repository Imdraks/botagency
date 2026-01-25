-- First, update existing quotes to use billing_clients.id instead of clients.id
-- The billing_client with crm_client_id=4 has id=1
UPDATE quotes SET client_id = 1 WHERE client_id = 4;

-- Now add the FK constraint
ALTER TABLE quotes ADD CONSTRAINT quotes_client_id_fkey 
    FOREIGN KEY (client_id) REFERENCES billing_clients(id) ON DELETE SET NULL;
