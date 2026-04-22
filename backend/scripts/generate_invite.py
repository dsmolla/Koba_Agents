import asyncio
import argparse
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_supabase

async def generate_invite(email: str):
    client = await get_supabase()
    
    code = str(uuid.uuid4())
    
    print(f"Generating invitation for {email}...")
    
    try:
        response = await client.table('invitation_codes').insert({
            "email": email,
            "code": code,
        }).execute()
        
        print("\nSuccess! Invitation created.")
        print("-" * 40)
        print(f"Email: {email}")
        print(f"Invitation Code: {code}")
        print("-" * 40)
        print("The user can now sign up using this exact email and code.")
        
    except Exception as e:
        print(f"\nError creating invitation: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an invitation code for a specific email.")
    parser.add_argument("email", type=str, help="The email address to invite")
    args = parser.parse_args()
    
    asyncio.run(generate_invite(args.email))
