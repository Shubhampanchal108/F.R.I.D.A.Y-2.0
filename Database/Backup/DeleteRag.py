
# ---------------- INTERACTIVE MAIN LOOP ---------------- #
if __name__ == "__main__":
    while True:
        print("\nOptions: [1] Search  [2] Save  [3] Delete  [4] Exit")
        choice = input("Select Option: ")

        if choice == "1":
            q = input("Search Query: ")
            results = search_vector_memory(q)
            for i, mem in enumerate(results):
                print(f"\nResult [{i+1}]: {mem['text']}\n   (Tags: {mem['metadata']['tags']})")

        elif choice == "2":
            txt = input("Enter text to save: ")
            print(save_longterm_memory(txt))

        # ---- DELETE LOGIC HERE ----
        elif choice == "3":
            q = input("Enter keyword to find data to delete: ")
            results = search_vector_memory(q, top_k=5)

            if not results:
                print("❌ No matching memory found.")
                continue

            print(f"\nFound {len(results)} items. Which one do you want to delete?")
            
            # Results display karein index ke saath
            for i, mem in enumerate(results):
                print(f"[{i+1}] {mem['text']}  (Date: {mem['metadata']['timestamp'][:10]})")
            
            print("[0] Cancel")

            try:
                selection = int(input("\nEnter number to delete: "))
                
                if selection == 0:
                    print("🚫 Delete cancelled.")
                elif 1 <= selection <= len(results):
                    # User ne jo select kiya, uska ID nikalo
                    selected_memory = results[selection - 1]
                    mem_id = selected_memory['id']
                    
                    # Confirm karein
                    confirm = input(f"⚠️ Are you sure you want to delete: '{selected_memory['text'][:20]}...'? (y/n): ")
                    
                    if confirm.lower() == 'y':
                        if delete_memory_by_id(mem_id):
                            print("🗑️ Memory deleted successfully.")
                        else:
                            print("❌ Failed to delete.")
                    else:
                        print("🚫 Cancelled.")
                else:
                    print("❌ Invalid selection.")
            except ValueError:
                print("❌ Please enter a valid number.")

        elif choice == "4":
            break