-- Drop the incorrect FK
ALTER TABLE quotes DROP CONSTRAINT IF EXISTS quotes_client_id_fkey;

-- Add the correct FK to billing_clients
ALTER TABLE quotes ADD CONSTRAINT quotes_client_id_fkey 
    FOREIGN KEY (client_id) REFERENCES billing_clients(id) ON DELETE SET NULL;

-- Same for invoices
ALTER TABLE invoices DROP CONSTRAINT IF EXISTS invoices_client_id_fkey;
ALTER TABLE invoices ADD CONSTRAINT invoices_client_id_fkey 
    FOREIGN KEY (client_id) REFERENCES billing_clients(id) ON DELETE SET NULL;
