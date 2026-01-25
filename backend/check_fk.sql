SELECT conname, conrelid::regclass, confrelid::regclass 
FROM pg_constraint 
WHERE conrelid::regclass::text = 'quotes' AND contype = 'f';
